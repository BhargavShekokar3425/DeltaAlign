"""Persistent exact dense costs: normalize dirty features and refresh disjoint blocks."""
from dataclasses import dataclass
import numpy as np
from scipy.spatial.distance import cdist


@dataclass
class CostCache:
    source: np.ndarray
    target: np.ndarray
    scale: np.ndarray
    costs: np.ndarray

    @classmethod
    def initialize(cls, source, target, scale):
        scale = np.asarray(scale,dtype=float).copy()
        if source.shape != target.shape or source.ndim != 2 or scale.shape != (source.shape[1],) or not np.all(np.isfinite(scale)) or np.any(scale<=0):
            raise ValueError('Expected equal feature matrices and finite positive scale')
        a,b=source/scale,target/scale
        return cls(a,b,scale,cdist(a,b,'sqeuclidean'))

    @property
    def normalized_feature_bytes(self):
        return self.source.nbytes+self.target.nbytes

    def update(self, source, target, changed_source, changed_target):
        """Mutate owned arrays; caller must supply complete actual dirty sets."""
        if source.shape != self.source.shape or target.shape != self.target.shape:
            raise ValueError('Feature dimensions must stay fixed')
        n=len(source)
        rows=np.asarray(sorted(set(changed_source)),dtype=int)
        columns=np.asarray(sorted(set(changed_target)),dtype=int)
        if np.any(rows<0) or np.any(rows>=n) or np.any(columns<0) or np.any(columns>=n):
            raise ValueError('Invalid dirty row/column')
        self.source[rows]=source[rows]/self.scale
        self.target[columns]=target[columns]/self.scale
        if len(rows):
            self.costs[rows,:]=cdist(self.source[rows],self.target,'sqeuclidean')
        remaining=np.ones(n,dtype=bool);remaining[rows]=False
        unchanged=np.flatnonzero(remaining)
        if len(columns) and len(unchanged):
            self.costs[np.ix_(unchanged,columns)]=cdist(self.source[unchanged],self.target[columns],'sqeuclidean')
        return len(rows)*n+len(columns)*(n-len(rows))
