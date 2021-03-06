import os
import sys
import typing
from json import loads
import numpy as np
import pandas as pd

from nk_croc import *

from d3m.primitive_interfaces.base import PrimitiveBase, CallResult

from d3m import container, utils
from d3m.metadata import hyperparams, base as metadata_base, params

__author__ = 'Distil'
__version__ = '1.2.2'

Inputs = container.pandas.DataFrame
Outputs = container.pandas.DataFrame


class Params(params.Params):
    pass


class Hyperparams(hyperparams.Hyperparams):
    target_columns = hyperparams.Set(
        elements=hyperparams.Hyperparameter[str](''),
        default=(),
        max_size=sys.maxsize,
        min_size=0,
        semantic_types=['https://metadata.datadrivendiscovery.org/types/ControlParameter'],
        description='names of columns with image paths'
    )

    output_labels = hyperparams.Set(
        elements=hyperparams.Hyperparameter[str](''),
        default=(),
        max_size=sys.maxsize,
        min_size=0,
        semantic_types=['https://metadata.datadrivendiscovery.org/types/ControlParameter'],
        description='desired names for croc output columns'
    )


class croc(PrimitiveBase[Inputs, Outputs, Params, Hyperparams]):
    metadata = metadata_base.PrimitiveMetadata({
        # Simply an UUID generated once and fixed forever. Generated using "uuid.uuid4()".
        'id': "404fae2a-2f0a-4c9b-9ad2-fb1528990561",
        'version': __version__,
        'name': "croc",
        # Keywords do not have a controlled vocabulary. Authors can put here whatever they find suitable.
        'keywords': ['OCR', 'object detection', 'image analysis'],
        'source': {
            'name': __author__,
            'uris': [
                # Unstructured URIs.
                "https://github.com/NewKnowledge/croc-d3m-wrapper",
            ],
        },
        # A list of dependencies in order. These can be Python packages, system packages, or Docker images.
        # Of course Python packages can also have their own dependencies, but sometimes it is necessary to
        # install a Python package first to be even able to run setup.py of another package. Or you have
        # a dependency which is not on PyPi.
        "installation": [
              {
                  "type": "UBUNTU",
                  "package": "tesseract-ocr",
                  "version": "3.04.01-6"
              },
              {
                  "type": "UBUNTU",
                  "package": "libtesseract-dev",
                  "version": "3.04.01-6"
              },
              {
                  "type": "UBUNTU",
                  "package": "libleptonica-dev",
                  "version": "1.74.4-1"
              },
              {
                  "type": "PIP",
                  "package_uri": "git+https://github.com/NewKnowledge/nk_croc.git@155be671f66978084055915ed582efbd38a66651#egg=nk_croc"
              },
              {
                  "type": "PIP",
                  "package_uri": "git+https://github.com/NewKnowledge/croc-d3m-wrapper.git@{git_commit}#egg=CROCd3mWrapper".format(
                        git_commit=utils.current_git_commit(os.path.dirname(__file__))
                        ),
              }
        ],
        # The same path the primitive is registered with entry points in setup.py.
        'python_path': 'd3m.primitives.distil.croc',
        # Choose these from a controlled vocabulary in the schema. If anything is missing which would
        # best describe the primitive, make a merge request.
        "algorithm_types": [
            metadata_base.PrimitiveAlgorithmType.MULTILABEL_CLASSIFICATION
            ],
        "primitive_family": metadata_base.PrimitiveFamily.DIGITAL_IMAGE_PROCESSING
    })

    def __init__(self, *, hyperparams: Hyperparams)-> None:
        super().__init__(hyperparams=hyperparams)

    def fit(self) -> None:
        pass

    def get_params(self) -> Params:
        return self._params

    def set_params(self, *, params: Params) -> None:
        self.params = params

    def set_training_data(self, *, inputs: Inputs, outputs: Outputs) -> None:
        pass

    def produce(self, *, inputs: Inputs) -> CallResult[Outputs]:
        """
            Produce image object classification predictions and OCR for an
            image provided as an URI or filepath

        Parameters
        ----------
        inputs : pandas dataframe where a column is a pd.Series of image paths/URLs

        Returns
        -------
        output : A dataframe with objects, text and tokens, corresponding to the
            detected objects, raw text and tokens predicted to be in the 
            supplied images.
        """

        target_columns = self.hyperparams['target_columns']
        output_labels = self.hyperparams['output_labels']

        imagepath_df = inputs
        image_analyzer = Croc()

        for i, ith_column in enumerate(target_columns):
            # initialize an empty dataframe
            result_df = pd.DataFrame()
            output_label = output_labels[i]

            for image_path in imagepath_df.loc[:, ith_column]:
                jth_result = loads(
                    image_analyzer.predict(input_path=image_path))

                result_df = result_df.append(
                    {output_label + '_object_id': jth_result['objects']['id'],
                     output_label + '_object_label': jth_result['objects']['label'],
                     output_label + '_object_conf': jth_result['objects']['confidence'],
                     output_label + '_object_trees': jth_result['object_trees'],
                     output_label + '_tokens': jth_result['tokens'],
                     output_label + '_text': jth_result['text']},
                    ignore_index=True)

            imagepath_df = pd.concat(
                [imagepath_df.reset_index(drop=True), result_df], axis=1)

        return imagepath_df


if __name__ == '__main__':
    client = croc(hyperparams={'target_columns': ['test_column'],
                               'output_labels': ['test_column_prefix']})
    imagepath_df = pd.DataFrame(
        pd.Series(['http://i0.kym-cdn.com/photos/images/facebook/001/253/011/0b1.jpg',
                   'http://i0.kym-cdn.com/photos/images/facebook/001/253/011/0b1.jpg']))
    imagepath_df.columns = ['test_column']
    result = client.produce(inputs=imagepath_df)
    print(result.head)
