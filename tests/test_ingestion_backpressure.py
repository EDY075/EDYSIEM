"""Testes do controle de backpressure (high/low water marks com histerese)."""

from __future__ import annotations

import asyncio

import pytest

from edysiem.ingestion.backpressure import (
    BackpressureConfig,
    BackpressureController,
    BackpressureState,
)


def test_config_defaults() -> None:
    config = BackpressureConfig()
    assert config.high_water_mark == 8_000
    assert config.low_water_mark == 2_000


@pytest.mark.parametrize(
    ("high", "low"),
    [
        (0, 0),
        (-1, 1),
        (10, 0),
        (10, 11),
        (10, -1),
    ],
)
def test_config_validation_rejects_invalid_marks(high: int, low: int) -> None:
    with pytest.raises(ValueError, match="water_mark"):
        BackpressureConfig(high_water_mark=high, low_water_mark=low)


def test_initial_state_is_normal() -> None:
    controller = BackpressureController()
    assert controller.state is BackpressureState.NORMAL
    assert controller.is_paused() is False


def test_report_size_pauses_above_high_water_mark() -> None:
    controller = BackpressureController(BackpressureConfig(high_water_mark=100, low_water_mark=10))
    controller.report_size(99)
    assert controller.state is BackpressureState.NORMAL
    controller.report_size(100)
    assert controller.state is BackpressureState.PAUSED


def test_report_size_resumes_below_low_water_mark() -> None:
    controller = BackpressureController(BackpressureConfig(high_water_mark=100, low_water_mark=10))
    controller.report_size(100)
    assert controller.is_paused()
    controller.report_size(11)
    assert controller.is_paused(), "histerese: entre LOW e HIGH permanece PAUSED"
    controller.report_size(10)
    assert controller.state is BackpressureState.NORMAL


def test_hysteresis_keeps_state_between_marks() -> None:
    controller = BackpressureController(BackpressureConfig(high_water_mark=100, low_water_mark=10))
    controller.report_size(150)
    assert controller.is_paused()
    controller.report_size(50)
    assert controller.is_paused()
    controller.report_size(9)
    assert not controller.is_paused()


def test_pause_and_resume_manual() -> None:
    controller = BackpressureController()
    controller.pause()
    assert controller.is_paused()
    controller.resume()
    assert not controller.is_paused()
    assert controller.state is BackpressureState.NORMAL


def test_report_size_rejects_negative() -> None:
    controller = BackpressureController()
    with pytest.raises(ValueError, match="negativo"):
        controller.report_size(-1)


def test_can_accept_semantics() -> None:
    controller = BackpressureController(BackpressureConfig(high_water_mark=100, low_water_mark=10))
    assert controller.can_accept(0) is True
    assert controller.can_accept(99) is True
    assert controller.can_accept(100) is False
    controller.report_size(100)
    assert controller.is_paused()
    assert controller.can_accept(0) is False, "paused nunca aceita"


def test_wait_until_resumed_returns_immediately_when_normal() -> None:
    controller = BackpressureController()
    result = asyncio.run(controller.wait_until_resumed(timeout=0.01))
    assert result is True


def test_wait_until_resumed_blocks_then_resumes() -> None:
    controller = BackpressureController()
    controller.pause()

    async def scenario() -> bool:
        task = asyncio.create_task(controller.wait_until_resumed())
        await asyncio.sleep(0.01)
        assert not task.done()
        controller.resume()
        return await task

    assert asyncio.run(scenario()) is True


def test_wait_until_resumed_timeout_returns_false() -> None:
    controller = BackpressureController()
    controller.pause()
    result = asyncio.run(controller.wait_until_resumed(timeout=0.01))
    assert result is False


def test_report_size_wakes_waiter_cross_thread() -> None:
    """Transições NORMAL↔PAUSED vindo de outra thread notificam o waiter async.

    Cobre o ``loop.call_soon_threadsafe`` tanto no ``set`` (retomada) quanto
    no ``clear`` (pausa) do evento interno.
    """
    import threading
    import time

    controller = BackpressureController(BackpressureConfig(high_water_mark=100, low_water_mark=10))
    controller.pause()

    async def scenario() -> bool:
        task = asyncio.create_task(controller.wait_until_resumed(timeout=1.0))
        await asyncio.sleep(0.02)

        def worker() -> None:
            time.sleep(0.02)
            controller.report_size(5)  # PAUSED -> NORMAL (set cross-thread)
            time.sleep(0.02)
            controller.report_size(200)  # NORMAL -> PAUSED (clear cross-thread)

        thread = threading.Thread(target=worker)
        thread.start()
        result = await task
        thread.join()
        return result

    assert asyncio.run(scenario()) is True
    assert controller.is_paused() is True


def test_wait_until_resumed_reusable_in_same_loop() -> None:
    """O controller pode ser aguardado mais de uma vez no mesmo loop."""
    controller = BackpressureController()
    controller.pause()

    async def scenario() -> None:
        assert await controller.wait_until_resumed(timeout=0.01) is False
        controller.resume()
        assert await controller.wait_until_resumed(timeout=0.01) is True

    asyncio.run(scenario())


def test_runtime_error_on_second_loop() -> None:
    controller = BackpressureController()

    async def first() -> None:
        await controller.wait_until_resumed()

    asyncio.run(first())

    async def second() -> None:
        await controller.wait_until_resumed()

    with pytest.raises(RuntimeError):
        asyncio.run(second())
