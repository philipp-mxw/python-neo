"""
This module defines :class:`Segment`, a container for data sharing a common
time basis.

:class:`Segment` derives from :class:`Container`,
from :module:`neo.core.container`.
"""

from datetime import datetime
from copy import deepcopy


from neo.core.analogsignal import AnalogSignal
from neo.core.container import Container
from neo.core.objectlist import ObjectList
from neo.core.epoch import Epoch
from neo.core.event import Event
from neo.core.imagesequence import ImageSequence
from neo.core.irregularlysampledsignal import IrregularlySampledSignal
from neo.core.spiketrainlist import SpikeTrainList
from neo.core.view import ChannelView


class Segment(Container):
    """
    A container for data sharing a common time basis.

    A :class:`Segment` is a heterogeneous container for discrete or continuous
    data sharing a common clock (time basis) but not necessary the same
    sampling rate, start or end time.

    Parameters
    ----------
    name: str | None, default: None
        A label for the dataset.
    description: str | None, default: None
         Text description.
    file_origin: str | None, default: None
        Filesystem path or URL of the original data file.
    rec_datetime: datetime.datetime| None, default: None
        The date and time of the original recording
    index: int | None, default: None
        You can use this to define a temporal ordering of your Segment.
        For instance you could use this for trial numbers.
    annotations: dict | None,
        Other keyword annotations for the dataset

    Examples
    --------
    >>> from neo.core import Segment, SpikeTrain, AnalogSignal
    >>> from quantities import Hz, s
    >>>
    >>> seg = Segment(index=5)
    >>>
    >>> train0 = SpikeTrain(times=[.01, 3.3, 9.3], units='sec', t_stop=10)
    >>> seg.spiketrains.append(train0)
    >>>
    >>> train1 = SpikeTrain(times=[100.01, 103.3, 109.3], units='sec',
    ...                     t_stop=110)
    >>> seg.spiketrains.append(train1)
    >>>
    >>> sig0 = AnalogSignal(signal=[.01, 3.3, 9.3], units='uV',
    ...                     sampling_rate=1*Hz)
    >>> seg.analogsignals.append(sig0)
    >>>
    >>> sig1 = AnalogSignal(signal=[100.01, 103.3, 109.3], units='nA',
    ...                     sampling_period=.1*s)
    >>> seg.analogsignals.append(sig1)

    Notes
    -----

    Container of:
        :class:`Epoch`
        :class:`Event`
        :class:`AnalogSignal`
        :class:`IrregularlySampledSignal`
        :class:`SpikeTrain`

    """

    _data_child_objects = ("AnalogSignal", "Epoch", "Event", "IrregularlySampledSignal", "SpikeTrain", "ImageSequence")
    _parent_objects = ("Block",)
    _recommended_attrs = (
        ("file_datetime", datetime),
        ("rec_datetime", datetime),
        ("index", int),
    ) + Container._recommended_attrs
    _repr_pretty_containers = ("analogsignals",)

    def __init__(
        self,
        name=None,
        description=None,
        file_origin=None,
        file_datetime=None,
        rec_datetime=None,
        index=None,
        **annotations,
    ):
        """
        Initialize a new :class:`Segment` instance.
        """
        super().__init__(name=name, description=description, file_origin=file_origin, **annotations)

        self._analogsignals = ObjectList(AnalogSignal, parent=self)
        self._irregularlysampledsignals = ObjectList(IrregularlySampledSignal, parent=self)
        self._spiketrains = SpikeTrainList(parent=self)
        self._events = ObjectList(Event, parent=self)
        self._epochs = ObjectList(Epoch, parent=self)
        self._channelviews = ObjectList(ChannelView, parent=self)
        self._imagesequences = ObjectList(ImageSequence, parent=self)
        self.block = None

        self.file_datetime = file_datetime
        self.rec_datetime = rec_datetime
        self.index = index

    analogsignals = property(
        fget=lambda self: self._get_object_list("_analogsignals"),
        fset=lambda self, value: self._set_object_list("_analogsignals", value),
        doc="list of AnalogSignals contained in this segment",
    )

    irregularlysampledsignals = property(
        fget=lambda self: self._get_object_list("_irregularlysampledsignals"),
        fset=lambda self, value: self._set_object_list("_irregularlysampledsignals", value),
        doc="list of IrregularlySignals contained in this segment",
    )

    events = property(
        fget=lambda self: self._get_object_list("_events"),
        fset=lambda self, value: self._set_object_list("_events", value),
        doc="list of Events contained in this segment",
    )

    epochs = property(
        fget=lambda self: self._get_object_list("_epochs"),
        fset=lambda self, value: self._set_object_list("_epochs", value),
        doc="list of Epochs contained in this segment",
    )

    channelviews = property(
        fget=lambda self: self._get_object_list("_channelviews"),
        fset=lambda self, value: self._set_object_list("_channelviews", value),
        doc="list of ChannelViews contained in this segment",
    )

    imagesequences = property(
        fget=lambda self: self._get_object_list("_imagesequences"),
        fset=lambda self, value: self._set_object_list("_imagesequences", value),
        doc="list of ImageSequences contained in this segment",
    )

    spiketrains = property(
        fget=lambda self: self._get_object_list("_spiketrains"),
        fset=lambda self, value: self._set_object_list("_spiketrains", value),
        doc="list of SpikeTrains contained in this segment",
    )

    # t_start attribute is handled as a property so type checking can be done
    @property
    def t_start(self):
        """
        Time when first signal begins.

        Returns
        -------
        t_start: float | None
            Returns the starting time if exists otherwise None
        """
        t_starts = [sig.t_start for sig in self.analogsignals + self.spiketrains + self.irregularlysampledsignals]

        for e in self.epochs + self.events:
            if hasattr(e, "t_start"):  # in case of proxy objects
                t_starts += [e.t_start]
            elif len(e) > 0:
                t_starts += [e.times[0]]

        # t_start is not defined if no children are present
        if len(t_starts) == 0:
            return None

        t_start = min(t_starts)
        return t_start

    # t_stop attribute is handled as a property so type checking can be done
    @property
    def t_stop(self):
        """
        Time when last signal ends.

        Returns
        -------
        t_stop: float | None
            Returns the stopping time if exists otherwise None
        """
        t_stops = [sig.t_stop for sig in self.analogsignals + self.spiketrains + self.irregularlysampledsignals]

        for e in self.epochs + self.events:
            if hasattr(e, "t_stop"):  # in case of proxy objects
                t_stops += [e.t_stop]
            elif len(e) > 0:
                t_stops += [e.times[-1]]

        # t_stop is not defined if no children are present
        if len(t_stops) == 0:
            return None

        t_stop = max(t_stops)
        return t_stop

    def time_slice(self, t_start=None, t_stop=None, reset_time=False, **kwargs):
        """
        Creates a time slice of a Segment containing slices of all child
        objects.

        Parameters
        ----------
        t_start: Quantity
            Starting time of the sliced time window.
        t_stop: Quantity
            Stop time of the sliced time window.
        reset_time: bool, optional, default: False
            If True the time stamps of all sliced objects are set to fall
            in the range from t_start to t_stop.
            If False, original time stamps are retained.
        **kwargs
            Additional keyword arguments used for initialization of the sliced
            Segment object.

        Returns
        -------
        subseg: Segment
            Temporal slice of the original Segment from t_start to t_stop.
        """
        subseg = Segment(**kwargs)

        for attr in ["file_datetime", "rec_datetime", "index", "name", "description", "file_origin"]:
            setattr(subseg, attr, getattr(self, attr))

        subseg.annotations = deepcopy(self.annotations)

        if t_start is None:
            t_start = self.t_start
        if t_stop is None:
            t_stop = self.t_stop

        t_shift = -t_start

        # cut analogsignals and analogsignalarrays
        for ana_id in range(len(self.analogsignals)):
            if hasattr(self.analogsignals[ana_id], "_rawio"):
                ana_time_slice = self.analogsignals[ana_id].load(time_slice=(t_start, t_stop))
            else:
                ana_time_slice = self.analogsignals[ana_id].time_slice(t_start, t_stop)
            if reset_time:
                ana_time_slice = ana_time_slice.time_shift(t_shift)
            subseg.analogsignals.append(ana_time_slice)

        # cut irregularly sampled signals
        for irr_id in range(len(self.irregularlysampledsignals)):
            if hasattr(self.irregularlysampledsignals[irr_id], "_rawio"):
                ana_time_slice = self.irregularlysampledsignals[irr_id].load(time_slice=(t_start, t_stop))
            else:
                ana_time_slice = self.irregularlysampledsignals[irr_id].time_slice(t_start, t_stop)
            if reset_time:
                ana_time_slice = ana_time_slice.time_shift(t_shift)
            subseg.irregularlysampledsignals.append(ana_time_slice)

        # cut spiketrains
        for st_id in range(len(self.spiketrains)):
            if hasattr(self.spiketrains[st_id], "_rawio"):
                st_time_slice = self.spiketrains[st_id].load(time_slice=(t_start, t_stop))
            else:
                st_time_slice = self.spiketrains[st_id].time_slice(t_start, t_stop)
            if reset_time:
                st_time_slice = st_time_slice.time_shift(t_shift)
            subseg.spiketrains.append(st_time_slice)

        # cut events
        for ev_id in range(len(self.events)):
            if hasattr(self.events[ev_id], "_rawio"):
                ev_time_slice = self.events[ev_id].load(time_slice=(t_start, t_stop))
            else:
                ev_time_slice = self.events[ev_id].time_slice(t_start, t_stop)
            if reset_time:
                ev_time_slice = ev_time_slice.time_shift(t_shift)
            # appending only non-empty events
            if len(ev_time_slice):
                subseg.events.append(ev_time_slice)

        # cut epochs
        for ep_id in range(len(self.epochs)):
            if hasattr(self.epochs[ep_id], "_rawio"):
                ep_time_slice = self.epochs[ep_id].load(time_slice=(t_start, t_stop))
            else:
                ep_time_slice = self.epochs[ep_id].time_slice(t_start, t_stop)
            if reset_time:
                ep_time_slice = ep_time_slice.time_shift(t_shift)
            # appending only non-empty epochs
            if len(ep_time_slice):
                subseg.epochs.append(ep_time_slice)

        subseg.check_relationships()

        return subseg
