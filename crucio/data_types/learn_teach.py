from abc import abstractmethod
from typing import Optional, TypeVar, Hashable, Generic, Any

T = TypeVar('T', bound=Hashable)
K = TypeVar('K')


class Learner(Generic[T, K]):
    @abstractmethod
    def understand(self, example: T) -> Optional[K]:
        pass

    @abstractmethod
    def learn(self, example: T):
        pass


class Teacher(Generic[T]):

    @abstractmethod
    def teach(self, learner: Learner[T, Any]) -> Optional[T]:
        pass


def teach(teacher: Teacher[T], learner: Learner[T, K]):
    while True:
        example = teacher.teach(learner)
        if example is None:
            break
        learner.learn(example)
