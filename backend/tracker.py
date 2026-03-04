"""
Centroid-based vehicle tracker.
Assigns persistent IDs to vehicles across frames so each
physical vehicle is counted only ONCE in a video.
"""
from collections import OrderedDict
import numpy as np
from scipy.spatial import distance as dist


class CentroidTracker:
    """
    Lightweight centroid tracker.
    Tracks objects by matching current detections to existing tracked
    centroids using Euclidean distance.
    """

    def __init__(self, max_disappeared: int = 40, max_distance: int = 80):
        """
        Parameters
        ----------
        max_disappeared : int
            Frames an object can be missing before it is deregistered.
        max_distance : int
            Max pixel distance to match a centroid to an existing object.
        """
        self.next_id       = 0
        self.objects: OrderedDict[int, np.ndarray] = OrderedDict()   # id → centroid
        self.classes:  dict[int, str]              = {}               # id → class name
        self.disappeared: dict[int, int]           = {}               # id → frames missing
        self.seen_ids:    set[int]                 = set()            # all IDs ever assigned
        self.max_disappeared = max_disappeared
        self.max_distance    = max_distance

    # ── internal ───────────────────────────────────────────────────────────────

    def _register(self, centroid: np.ndarray, class_name: str):
        self.objects[self.next_id]    = centroid
        self.classes[self.next_id]    = class_name
        self.disappeared[self.next_id] = 0
        self.seen_ids.add(self.next_id)
        self.next_id += 1

    def _deregister(self, object_id: int):
        del self.objects[object_id]
        del self.classes[object_id]
        del self.disappeared[object_id]

    # ── public ─────────────────────────────────────────────────────────────────

    def update(self, detections: list[dict]) -> dict[int, np.ndarray]:
        """
        Parameters
        ----------
        detections : list of dicts with keys:
            bbox       : (x1, y1, x2, y2)
            class_name : str

        Returns
        -------
        OrderedDict {id: centroid}  — currently active objects only
        """
        # ── No detections ──────────────────────────────────────────────────────
        if len(detections) == 0:
            for obj_id in list(self.disappeared.keys()):
                self.disappeared[obj_id] += 1
                if self.disappeared[obj_id] > self.max_disappeared:
                    self._deregister(obj_id)
            return self.objects

        # ── Build (centroid, class_name) arrays ───────────────────────────────
        input_centroids   = np.zeros((len(detections), 2), dtype="int")
        input_class_names = []
        for i, det in enumerate(detections):
            x1, y1, x2, y2 = det["bbox"]
            input_centroids[i] = ((x1 + x2) // 2, (y1 + y2) // 2)
            input_class_names.append(det["class_name"])

        # ── No existing objects → register all ────────────────────────────────
        if len(self.objects) == 0:
            for i in range(len(input_centroids)):
                self._register(input_centroids[i], input_class_names[i])
            return self.objects

        # ── Match by Euclidean distance ───────────────────────────────────────
        object_ids       = list(self.objects.keys())
        object_centroids = list(self.objects.values())

        D = dist.cdist(np.array(object_centroids), input_centroids)

        rows = D.min(axis=1).argsort()
        cols = D.argmin(axis=1)[rows]

        used_rows, used_cols = set(), set()
        for row, col in zip(rows, cols):
            if row in used_rows or col in used_cols:
                continue
            if D[row, col] > self.max_distance:
                continue
            obj_id = object_ids[row]
            self.objects[obj_id]     = input_centroids[col]
            self.disappeared[obj_id] = 0
            used_rows.add(row)
            used_cols.add(col)

        # ── Handle unmatched rows/cols ─────────────────────────────────────────
        unused_rows = set(range(D.shape[0])) - used_rows
        unused_cols = set(range(D.shape[1])) - used_cols

        for row in unused_rows:
            obj_id = object_ids[row]
            self.disappeared[obj_id] += 1
            if self.disappeared[obj_id] > self.max_disappeared:
                self._deregister(obj_id)

        for col in unused_cols:
            self._register(input_centroids[col], input_class_names[col])

        return self.objects

    # ── Stats ──────────────────────────────────────────────────────────────────

    def get_unique_counts(self) -> dict[str, int]:
        """
        Count unique vehicles seen across the entire video so far,
        grouped by class name.
        """
        counts: dict[str, int] = {}
        for obj_id in self.seen_ids:
            cls = self.classes.get(obj_id)
            if cls:
                counts[cls] = counts.get(cls, 0) + 1
        return counts

    def reset(self):
        """Reset tracker state (call between videos)."""
        self.__init__(self.max_disappeared, self.max_distance)
