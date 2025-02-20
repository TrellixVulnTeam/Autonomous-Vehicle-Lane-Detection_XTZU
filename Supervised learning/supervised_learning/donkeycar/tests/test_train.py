import pytest
import tarfile
import os
import numpy as np
from collections import defaultdict, namedtuple
from typing import Callable

from donkeycar.pipeline.training import train, BatchSequence
from donkeycar.config import Config
from donkeycar.pipeline.types import TubDataset, TubRecord
from donkeycar.utils import get_model_by_type, normalize_image

Data = namedtuple('Data', ['type', 'name', 'convergence', 'pretrained'])


@pytest.fixture
def config() -> Config:
    """ Config for the test with relevant parameters"""
    cfg = Config()
    cfg.BATCH_SIZE = 64
    cfg.TRAIN_TEST_SPLIT = 0.8
    cfg.IMAGE_H = 120
    cfg.IMAGE_W = 160
    cfg.IMAGE_DEPTH = 3
    cfg.PRINT_MODEL_SUMMARY = True
    cfg.EARLY_STOP_PATIENCE = 1000
    cfg.MAX_EPOCHS = 5
    cfg.MODEL_CATEGORICAL_MAX_THROTTLE_RANGE = 0.8
    cfg.VERBOSE_TRAIN = True
    cfg.MIN_DELTA = 0.0005
    return cfg


@pytest.fixture(scope='session')
def car_dir(tmpdir_factory):
    """ Creating car dir with sub dirs and extracting tub """
    dir = tmpdir_factory.mktemp('mycar')
    os.mkdir(os.path.join(dir, 'models'))
    # extract tub.tar.gz into temp car_dir/tub
    this_dir = os.path.dirname(os.path.abspath(__file__))
    with tarfile.open(os.path.join(this_dir, 'tub', 'tub.tar.gz')) as file:
        def is_within_directory(directory, target):
            
            abs_directory = os.path.abspath(directory)
            abs_target = os.path.abspath(target)
        
            prefix = os.path.commonprefix([abs_directory, abs_target])
            
            return prefix == abs_directory
        
        def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
        
            for member in tar.getmembers():
                member_path = os.path.join(path, member.name)
                if not is_within_directory(path, member_path):
                    raise Exception("Attempted Path Traversal in Tar File")
        
            tar.extractall(path, members, numeric_owner=numeric_owner) 
            
        
        safe_extract(file, dir)
    return dir


# define the test data
d1 = Data(type='linear', name='lin1', convergence=0.6, pretrained=None)
d2 = Data(type='categorical', name='cat1', convergence=0.9, pretrained=None)
d3 = Data(type='inferred', name='inf1', convergence=0.9, pretrained=None)
d4 = Data(type='latent', name='lat1', convergence=0.5, pretrained=None)
d5 = Data(type='latent', name='lat2', convergence=0.5, pretrained='lat1')
test_data = [d1, d2, d3]


@pytest.mark.skipif("GITHUB_ACTIONS" in os.environ,
                    reason='Suppress training test in CI')
@pytest.mark.parametrize('data', test_data)
def test_train(config: Config, car_dir: str, data: Data) -> None:
    """
    Testing convergence of the linear an categorical models

    :param config:          donkey config
    :param car_dir:         car directory (this is a temp dir)
    :param data:            test case data
    :return:                None
    """
    def pilot_path(name):
        pilot_name = f'pilot_{name}.h5'
        return os.path.join(car_dir, 'models', pilot_name)

    if data.pretrained:
        config.LATENT_TRAINED = pilot_path(data.pretrained)
    tub_dir = os.path.join(car_dir, 'tub')
    history = train(config, tub_dir, pilot_path(data.name), data.type)
    loss = history.history['loss']
    # check loss is converging
    assert loss[-1] < loss[0] * data.convergence


filters = [lambda r: r.underlying['user/throttle'] > 0.5,
           lambda r: r.underlying['user/angle'] < 0,
           lambda r: r.underlying['user/throttle'] < 0.6 and
                     r.underlying['user/angle'] > -0.5]


@pytest.mark.parametrize('model_type', ['linear', 'categorical', 'inferred'])
@pytest.mark.parametrize('train_filter', filters)
def test_training_pipeline(config: Config, model_type: str, car_dir: str,
                           train_filter: Callable[[TubRecord], bool]) -> None:
    """
    Testing consistency of the model interfaces and data used in training
    pipeline.

    :param config:                  donkey config
    :param model_type:              test specification of model type
    :param tub_dir:                 tub directory (car_dir/tub)
    :param train_filter:            filter for records
    :return:                        None
    """
    config.TRAIN_FILTER = train_filter
    kl = get_model_by_type(model_type, config)
    tub_dir = os.path.join(car_dir, 'tub')
    # don't shuffle so we can identify data for testing
    config.TRAIN_FILTER = train_filter
    dataset = TubDataset(config, [tub_dir], shuffle=False)
    training_records, validation_records = dataset.train_test_split()
    seq = BatchSequence(kl, config, training_records, True)
    data_train = seq.create_tf_data()
    num_whole_batches = len(training_records) // config.BATCH_SIZE
    # this takes all batches into one list
    tf_batch = list(data_train.take(num_whole_batches).as_numpy_iterator())
    it = iter(training_records)
    for xy_batch in tf_batch:
        # extract x and y values from records, asymmetric in x and y b/c x
        # requires image manipulations
        batch_records = [next(it) for _ in range(config.BATCH_SIZE)]
        records_x = [kl.x_translate(normalize_image(kl.x_transform(r))) for
                     r in batch_records]
        records_y = [kl.y_translate(kl.y_transform(r)) for r in
                     batch_records]
        # from here all checks are symmetrical between x and y
        for batch, o_type, records \
                in zip(xy_batch, kl.output_types(), (records_x, records_y)):
            # check batch dictionary have expected keys
            assert batch.keys() == o_type.keys(), \
                'batch keys need to match models output types'
            # convert record values into arrays of batch size
            values = defaultdict(list)
            for r in records:
                for k, v in r.items():
                    values[k].append(v)
            # now convert arrays of floats or numpy arrays into numpy arrays
            np_dict = dict()
            for k, v in values.items():
                np_dict[k] = np.array(v)
            # compare record values with values from tf.data
            for k, v in batch.items():
                assert np.isclose(v, np_dict[k]).all()

