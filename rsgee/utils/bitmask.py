from math import log, ceil
from functools import reduce
import ee
from rsgee.band import Band


def build_bitmasks(states_mapping, start_position=0):
    bitmasks = {}

    def build(left_shift, state):
        options = [f'{state}.{option}' for option in states_mapping[state]]
        options_bitmasks = {option: i << left_shift for i, option in enumerate(options)}
        bitmasks.update(options_bitmasks)

        return left_shift + ceil(log(len(options), 2))

    reduce(build, states_mapping.keys(), start_position)

    return bitmasks


def get_qa_score(quality_band, bitmasks_scores):
    best_score = quality_band.gte(0).int().rename('mask')

    def score(params):
        params = ee.List(params)
        score_value = params.getNumber(0)
        bitmasks = ee.List(params.get(1))

        mask = get_mask_from_bitmask_list(quality_band, bitmasks, 'or')
        scored_mask = mask.multiply(score_value)

        return scored_mask.int().rename('mask')

    bitmasks_scores = list(bitmasks_scores.items())

    scored_list = ee.List(bitmasks_scores).map(score).cat([best_score])
    scored = ee.ImageCollection(scored_list).max().rename(Band.QA_SCORE)

    return scored


def get_mask_from_bitmask_list(quality_band, bitmasks, reducer='or', reverse=False):
    reducer = {
        'and': ee.Reducer.allNonZero,
        'or': ee.Reducer.anyNonZero
    }[reducer]

    bitmasks = ee.Image.constant(bitmasks)

    mask = (quality_band
            .bitwiseAnd(bitmasks)
            .eq(bitmasks)
            .reduce(reducer()))

    if reverse:
        mask = mask.Not()

    return mask

def get_mask_from_bitmask(quality_band, bitmask):
    bitmask = ee.Image.constant(bitmask)
    return quality_band.bitwiseAnd(bitmask).eq(bitmask)
