from crucio.config import Config
from crucio.utils.sub_con import Subs, Cons, SubsK, ConsK
from crucio.data_types.distribution.matrix import DistributionalMatrix
from crucio.utils.log import Logger, terminal
from crucio.utils.statistics import timer


@timer('buildDM')
def build_dm(examples, oracle, logger:Logger = terminal):
    if Config.localConSub == 0:
        subs = Subs(examples)
        cons = Cons(examples)
    else:
        subs = SubsK(examples, Config.localConSub)
        cons = ConsK(examples, Config.localConSub)
    logger.print('Sub=',len(subs),'Con=',len(cons),'Total=',len(subs)*len(cons))
    return DistributionalMatrix(subs, cons, oracle,logger)
