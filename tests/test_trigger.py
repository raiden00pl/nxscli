from threading import Lock

import pytest  # type: ignore

from nxscli.trigger import (
    DTriggerConfig,
    ETriggerType,
    TriggerHandler,
    trigger_from_str,
)

# we want to run TriggerHandler tests without concurency
global_lock = Lock()


def test_triggerfromstr():
    x = trigger_from_str([("off", None)])
    assert x.ttype == ETriggerType.ALWAYS_OFF
    assert x.srcchan is None
    assert x.hoffset == 0
    assert x.level is None

    x = trigger_from_str([("on", None)])
    assert x.ttype == ETriggerType.ALWAYS_ON
    assert x.srcchan is None
    assert x.hoffset == 0
    assert x.level is None

    x = trigger_from_str([("er", None), "100", "10"])
    assert x.ttype == ETriggerType.EDGE_RISING
    assert x.hoffset == 100
    assert x.level == 10

    x = trigger_from_str([("ef", None), "200", "20"])
    assert x.ttype == ETriggerType.EDGE_FALLING
    assert x.srcchan is None
    assert x.hoffset == 200
    assert x.level == 20

    x = trigger_from_str([("ef", 1), "200", "20"])
    assert x.ttype == ETriggerType.EDGE_FALLING
    assert x.srcchan == 1
    assert x.hoffset == 200
    assert x.level == 20


def test_triggerhandle_init():
    with global_lock:
        assert len(TriggerHandler._instances) == 0

        dtc0 = DTriggerConfig(ETriggerType.ALWAYS_OFF)
        th0 = TriggerHandler(0, dtc0)

        assert th0.chan == 0
        assert th0._src is None
        assert th0._cross == []
        assert len(th0._instances) == 1

        # we can register many trigger handlers for the same channel
        dtc0_1 = DTriggerConfig(ETriggerType.ALWAYS_ON)
        th0_1 = TriggerHandler(0, dtc0_1)

        assert th0_1.chan == 0
        assert th0_1._src is None
        assert th0_1._cross == []

        assert len(th0._instances) == 2
        assert len(th0_1._instances) == 2

        # no source channel registerd - raise
        dtcx = DTriggerConfig(ETriggerType.ALWAYS_OFF, srcchan=2)
        with pytest.raises(AttributeError):
            _ = TriggerHandler(1, dtcx)

        assert th0.chan == 0
        assert th0._src is None
        assert th0._cross == []

        assert len(th0._instances) == 2
        assert len(th0_1._instances) == 2

        # valid cross-channel source trigger
        dtc1 = DTriggerConfig(ETriggerType.ALWAYS_OFF, srcchan=0)
        th1 = TriggerHandler(1, dtc1)

        assert th0.chan == 0
        assert th0._src is None

        assert th0_1.chan == 0
        assert th0_1._src is None

        assert th1.chan == 1
        assert th1._src is not None
        assert th1 in th1._src._cross
        assert th1._cross == []

        assert len(th0._instances) == 3
        assert len(th0_1._instances) == 3
        assert len(th1._instances) == 3

        # another valid cross-channel source trigger
        dtc2 = DTriggerConfig(ETriggerType.ALWAYS_OFF, srcchan=0)
        th2 = TriggerHandler(2, dtc2)

        # another valid cross-channel source trigger
        dtc3 = DTriggerConfig(ETriggerType.ALWAYS_OFF, srcchan=0)
        th3 = TriggerHandler(3, dtc3)

        assert len(th0._instances) == 5
        assert len(th0_1._instances) == 5
        assert len(th1._instances) == 5
        assert len(th2._instances) == 5
        assert len(th3._instances) == 5

        assert th2._src is not None
        assert th2 in th2._src._cross

        assert th3._src is not None
        assert th3 in th3._src._cross

        # clean up
        TriggerHandler.cls_cleanup()


def test_triggerhandle_init2():
    with global_lock:
        assert len(TriggerHandler._instances) == 0

        dtc0 = DTriggerConfig(ETriggerType.ALWAYS_OFF)
        th0 = TriggerHandler(0, dtc0)

        # there should be no references to the previous test
        assert len(th0._instances) == 1

        # clean up
        TriggerHandler.cls_cleanup()


def test_triggerhandle_alwaysoff():
    with global_lock:
        assert len(TriggerHandler._instances) == 0

        # always off
        dtc = DTriggerConfig(ETriggerType.ALWAYS_OFF)
        th = TriggerHandler(0, dtc)
        assert len(th._instances) == 1
        for _ in range(100):
            din = [(1,), (2,), (3,)]
            dout = th.data_triggered(din)
            assert dout == []

        # clean up
        TriggerHandler.cls_cleanup()


def test_triggerhandle_alwayson():
    with global_lock:
        assert len(TriggerHandler._instances) == 0

        # always on
        dtc = DTriggerConfig(ETriggerType.ALWAYS_ON)
        th = TriggerHandler(0, dtc)
        assert len(th._instances) == 1
        for _ in range(100):
            din = [(1,), (2,), (3,)]
            dout = th.data_triggered(din)
            assert dout == [(1,), (2,), (3,)]

        # clean up
        TriggerHandler.cls_cleanup()


def test_triggerhandle_edgerising1():
    with global_lock:
        assert len(TriggerHandler._instances) == 0

        # rising edge on 0
        hoffset = 0
        level = 0
        dtc = DTriggerConfig(
            ETriggerType.EDGE_RISING, hoffset=hoffset, level=level
        )
        th = TriggerHandler(0, dtc)

        assert len(th._instances) == 1

        din = [((0,), ()), ((0,), ()), ((0,), ())]
        dout = th.data_triggered(din)
        assert dout == []

        din = [((0,), ()), ((0,), ()), ((0,), ())]
        dout = th.data_triggered(din)
        assert dout == []

        din = [((-1,), ()), ((-2,), ()), ((-3,), ())]
        dout = th.data_triggered(din)
        assert dout == []

        din = [((-3,), ()), ((-3,), ()), ((-3,), ())]
        dout = th.data_triggered(din)
        assert dout == []

        # triggered - rising edge on 0
        din = [((0,), ()), ((1,), ()), ((2,), ())]
        dout = th.data_triggered(din)
        assert dout == [((0,), ()), ((1,), ()), ((2,), ())]

        din = [((3,), ()), ((4,), ()), ((5,), ())]
        dout = th.data_triggered(din)
        assert dout == [((3,), ()), ((4,), ()), ((5,), ())]

        din = [((0,), ()), ((0,), ()), ((0,), ())]
        dout = th.data_triggered(din)
        assert dout == [((0,), ()), ((0,), ()), ((0,), ())]

        din = [((0,), ()), ((-1,), ()), ((-2,), ())]
        dout = th.data_triggered(din)
        assert dout == [((0,), ()), ((-1,), ()), ((-2,), ())]

        # clean up
        TriggerHandler.cls_cleanup()


def test_triggerhandle_edgerising2():
    with global_lock:
        assert len(TriggerHandler._instances) == 0

        # rising edge on 5
        hoffset = 0
        level = 5
        dtc = DTriggerConfig(
            ETriggerType.EDGE_RISING, hoffset=hoffset, level=level
        )
        th = TriggerHandler(0, dtc)

        assert len(th._instances) == 1

        din = [((0,), ()), ((0,), ()), ((0,), ())]
        dout = th.data_triggered(din)
        assert dout == []

        din = [((0,), ()), ((0,), ()), ((0,), ())]
        dout = th.data_triggered(din)
        assert dout == []

        din = [((-1,), ()), ((-2,), ()), ((-3,), ())]
        dout = th.data_triggered(din)
        assert dout == []

        din = [((-4,), ()), ((-3,), ()), ((-2,), ())]
        dout = th.data_triggered(din)
        assert dout == []

        din = [((0,), ()), ((1,), ()), ((2,), ())]
        dout = th.data_triggered(din)
        assert dout == []

        # triggered
        din = [((4,), ()), ((5,), ()), ((6,), ()), ((7,), ())]
        dout = th.data_triggered(din)
        assert dout == [((5,), ()), ((6,), ()), ((7,), ())]

        din = [((3,), ()), ((4,), ()), ((5,), ())]
        dout = th.data_triggered(din)
        assert dout == [((3,), ()), ((4,), ()), ((5,), ())]

        din = [((0,), ()), ((0,), ()), ((0,), ())]
        dout = th.data_triggered(din)
        assert dout == [((0,), ()), ((0,), ()), ((0,), ())]

        din = [((0,), ()), ((-1,), ()), ((-2,), ())]
        dout = th.data_triggered(din)
        assert dout == [((0,), ()), ((-1,), ()), ((-2,), ())]

        # clean up
        TriggerHandler.cls_cleanup()


def test_triggerhandle_edgefalling1():
    with global_lock:
        assert len(TriggerHandler._instances) == 0

        # falling edge on 0
        hoffset = 0
        level = 0
        dtc = DTriggerConfig(
            ETriggerType.EDGE_FALLING, hoffset=hoffset, level=level
        )
        th = TriggerHandler(0, dtc)

        assert len(th._instances) == 1

        din = [((0,), ()), ((0,), ()), ((0,), ())]
        dout = th.data_triggered(din)
        assert dout == []

        din = [((0,), ()), ((0,), ()), ((0,), ())]
        dout = th.data_triggered(din)
        assert dout == []

        din = [((0,), ()), ((1,), ()), ((2,), ())]
        dout = th.data_triggered(din)
        assert dout == []

        # triggered
        din = [((2,), ()), ((1,), ()), ((0,), ())]
        dout = th.data_triggered(din)
        assert dout == [((0,), ())]

        din = [((-1,), ()), ((-2,), ()), ((-3,), ())]
        dout = th.data_triggered(din)
        assert dout == [((-1,), ()), ((-2,), ()), ((-3,), ())]

        din = [((2,), ()), ((1,), ()), ((0,), ())]
        dout = th.data_triggered(din)
        assert dout == [((2,), ()), ((1,), ()), ((0,), ())]

        din = [((0,), ()), ((0,), ()), ((0,), ())]
        dout = th.data_triggered(din)
        assert dout == [((0,), ()), ((0,), ()), ((0,), ())]

        din = [((1,), ()), ((2,), ()), ((3,), ())]
        dout = th.data_triggered(din)
        assert dout == [((1,), ()), ((2,), ()), ((3,), ())]

        din = [((4,), ()), ((5,), ()), ((6,), ())]
        dout = th.data_triggered(din)
        assert dout == [((4,), ()), ((5,), ()), ((6,), ())]

        # clean up
        TriggerHandler.cls_cleanup()


def test_triggerhandle_edgefalling2():
    with global_lock:
        assert len(TriggerHandler._instances) == 0

        # falling edge on -5
        hoffset = 0
        level = -5
        dtc = DTriggerConfig(
            ETriggerType.EDGE_FALLING, hoffset=hoffset, level=level
        )
        th = TriggerHandler(0, dtc)

        assert len(th._instances) == 1

        din = [((0,), ()), ((0,), ()), ((0,), ())]
        dout = th.data_triggered(din)
        assert dout == []

        din = [((0,), ()), ((0,), ()), ((0,), ())]
        dout = th.data_triggered(din)
        assert dout == []

        din = [((0,), ()), ((1,), ()), ((2,), ())]
        dout = th.data_triggered(din)
        assert dout == []

        din = [((3,), ()), ((2,), ()), ((1,), ()), ((0,), ())]
        dout = th.data_triggered(din)
        assert dout == []

        din = [((-1,), ()), ((-2,), ()), ((-3,), ())]
        dout = th.data_triggered(din)
        assert dout == []

        # triggered
        din = [((-4,), ()), ((-5,), ()), ((-6,), ())]
        dout = th.data_triggered(din)
        assert dout == [((-5,), ()), ((-6,), ())]

        din = [((2,), ()), ((1,), ()), ((0,), ())]
        dout = th.data_triggered(din)
        assert dout == [((2,), ()), ((1,), ()), ((0,), ())]

        din = [((0,), ()), ((0,), ()), ((0,), ())]
        dout = th.data_triggered(din)
        assert dout == [((0,), ()), ((0,), ()), ((0,), ())]

        din = [((1,), ()), ((2,), ()), ((3,), ())]
        dout = th.data_triggered(din)
        assert dout == [((1,), ()), ((2,), ()), ((3,), ())]

        din = [((4,), ()), ((5,), ()), ((6,), ())]
        dout = th.data_triggered(din)
        assert dout == [((4,), ()), ((5,), ()), ((6,), ())]

        # clean up
        TriggerHandler.cls_cleanup()


def test_triggerhandle_chanxtochany_nohoffset():
    with global_lock:
        assert len(TriggerHandler._instances) == 0

        # chan0 - always off
        dtc0 = DTriggerConfig(ETriggerType.ALWAYS_OFF)
        th0 = TriggerHandler(0, dtc0)

        # chan1 - trigger on chan0 rising endge 4
        hoffset = 0
        level = 4
        srcchan = 0
        dtc1 = DTriggerConfig(
            ETriggerType.EDGE_RISING,
            srcchan=srcchan,
            hoffset=hoffset,
            level=level,
        )
        th1 = TriggerHandler(1, dtc1)

        assert len(th0._instances) == 2
        assert len(th1._instances) == 2

        din0 = [((0,), ()), ((1,), ()), ((2,), ())]
        dout0 = th0.data_triggered(din0)
        assert dout0 == []

        din1 = [((0,), ()), ((1,), ()), ((2,), ())]
        dout1 = th1.data_triggered(din1)
        assert dout1 == []

        din0 = [((1,), ()), ((0,), ()), ((-1,), ())]
        dout0 = th0.data_triggered(din0)
        assert dout0 == []

        din1 = [((3,), ()), ((4,), ()), ((5,), ())]
        dout1 = th1.data_triggered(din1)
        assert dout1 == []

        din0 = [((0,), ()), ((0,), ()), ((0,), ())]
        dout0 = th0.data_triggered(din0)
        assert dout0 == []

        din1 = [((4,), ()), ((3,), ()), ((2,), ())]
        dout1 = th1.data_triggered(din1)
        assert dout1 == []

        # th1 triggerd - but th0 is always off
        din0 = [((3,), ()), ((4,), ()), ((5,), ())]
        dout0 = th0.data_triggered(din0)
        assert dout0 == []

        din1 = [((10,), ()), ((11,), ()), ((12,), ())]
        dout1 = th1.data_triggered(din1)
        assert dout1 == [((10,), ()), ((11,), ()), ((12,), ())]

        din0 = [((0,), ()), ((0,), ()), ((0,), ())]
        dout0 = th0.data_triggered(din0)
        assert dout0 == []

        din1 = [((1,), ()), ((1,), ()), ((1,), ())]
        dout1 = th1.data_triggered(din1)
        assert dout1 == [((1,), ()), ((1,), ()), ((1,), ())]

        # th1 is now triggered
        din1 = [((1,), ()), ((1,), ()), ((1,), ())]
        dout1 = th1.data_triggered(din1)
        assert dout1 == [((1,), ()), ((1,), ()), ((1,), ())]

        din1 = [((-1,), ()), ((-1,), ()), ((-1,), ())]
        dout1 = th1.data_triggered(din1)
        assert dout1 == [((-1,), ()), ((-1,), ()), ((-1,), ())]

        # clean up
        TriggerHandler.cls_cleanup()


def test_triggerhandle_chanxtochany_hoffset():
    with global_lock:
        assert len(TriggerHandler._instances) == 0

        # chan0 - always off
        dtc0 = DTriggerConfig(ETriggerType.ALWAYS_OFF)
        th0 = TriggerHandler(0, dtc0)

        # chan1 - trigger on chan0 rising endge 4
        hoffset = 2
        level = 4
        srcchan = 0
        dtc1 = DTriggerConfig(
            ETriggerType.EDGE_RISING,
            srcchan=srcchan,
            hoffset=hoffset,
            level=level,
        )
        th1 = TriggerHandler(1, dtc1)

        assert len(th0._instances) == 2
        assert len(th1._instances) == 2

        din0 = [((0,), ()), ((1,), ()), ((2,), ())]
        dout0 = th0.data_triggered(din0)
        assert dout0 == []

        din1 = [((0,), ()), ((1,), ()), ((2,), ())]
        dout1 = th1.data_triggered(din1)
        assert dout1 == []

        din0 = [((1,), ()), ((0,), ()), ((-1,), ())]
        dout0 = th0.data_triggered(din0)
        assert dout0 == []

        din1 = [((3,), ()), ((4,), ()), ((5,), ())]
        dout1 = th1.data_triggered(din1)
        assert dout1 == []

        din0 = [((0,), ()), ((0,), ()), ((0,), ())]
        dout0 = th0.data_triggered(din0)
        assert dout0 == []

        din1 = [((4,), ()), ((3,), ()), ((2,), ())]
        dout1 = th1.data_triggered(din1)
        assert dout1 == []

        # th1 triggerd with hoffset - but th0 is always off
        din0 = [((3,), ()), ((4,), ()), ((5,), ())]
        dout0 = th0.data_triggered(din0)
        assert dout0 == []

        din1 = [((10,), ()), ((11,), ()), ((12,), ())]
        dout1 = th1.data_triggered(din1)
        assert dout1 == [
            ((3,), ()),
            ((2,), ()),
            ((10,), ()),
            ((11,), ()),
            ((12,), ()),
        ]

        din0 = [((0,), ()), ((0,), ()), ((0,), ())]
        dout0 = th0.data_triggered(din0)
        assert dout0 == []

        din1 = [((1,), ()), ((1,), ()), ((1,), ())]
        dout1 = th1.data_triggered(din1)
        assert dout1 == [((1,), ()), ((1,), ()), ((1,), ())]

        # th1 is now triggered
        din1 = [((1,), ()), ((1,), ()), ((1,), ())]
        dout1 = th1.data_triggered(din1)
        assert dout1 == [((1,), ()), ((1,), ()), ((1,), ())]

        din1 = [((-1,), ()), ((-1,), ()), ((-1,), ())]
        dout1 = th1.data_triggered(din1)
        assert dout1 == [((-1,), ()), ((-1,), ()), ((-1,), ())]

        # clean up
        TriggerHandler.cls_cleanup()


def test_triggerhandle_edgerising_hoffset():
    # TODO
    pass


def test_triggerhandle_chanxtochanx():
    pass


def test_triggerhandle_allthesame():
    pass