User-Defined Functions
======================

This section provides an overview of how you can create and use a custom user-defined function (UDF) in your queries. For example, you could write an UDF that wraps around a PyTorch model.


Part 1: Writing a custom UDF
-----

.. admonition:: Illustrative UDF implementation

    During each step, use `this UDF implementation <https://github.com/georgia-tech-db/eva/blob/master/eva/udfs/fastrcnn_object_detector.py>`_  as a reference.

1. Create a new file under `udfs/` folder and give it a descriptive name. eg: `fastrcnn_object_detector.py`, `midas_depth_estimator.py`. 

.. note::

    UDFs packaged along with EVA are located inside the `udfs <https://github.com/georgia-tech-db/eva/tree/master/eva/udfs>`_ folder.

2. Create a Python class that inherits from `PytorchClassifierAbstractUDF`.

* The `PytorchClassifierAbstractUDF` is a parent class that defines and implements standard methods for model inference.

* `_get_predictions()` - an abstract method that needs to be implemented in your child class.

* `classify()` - A  method that receives the frames and calls the `_get_predictions()` implemented in your child class. Based on GPU batch size, it also decides whether to split frames into chunks and performs the accumulation.

* Additionally, it contains methods that help in:

    * Moving tensors to GPU
    * Converting tensors to numpy arrays.
    * Defining the `forward()` function that gets called when the model is invoked.
    * Basic transformations.


You can however **choose to override** these methods depending on your requirements.

3.  A typical UDF class has the following components:

* `__init__()` constructor:

    * Define variables here that will be required across all methods.
    * Model loading happens here. You can choose to load custom models or models from torch.

        * Example of loading a custom model:
            .. code-block:: python

                custom_model_path = os.path.join(EVA_DIR, "data", "models", "vehicle_make_predictor", "car_recognition.pt")
                self.car_make_model = CarRecognitionModel()
                self.car_make_model.load_state_dict(torch.load(custom_model_path))
                self.car_make_model.eval()

        * Example of loading a torch model:
            .. code-block:: python

                self.model = torchvision.models.detection.fasterrcnn_resnet50_fpn(pretrained=True)
                self.model.eval()

* `labels()` method:

    * This should return a list of strings that your model aims to target.
    * The index of the list is the value predicted by your model.

* `_get_predictions()` method:

    * This is where all your model inference logic goes.
    * While doing the computations, keep in mind that each call of this method is with a batch of frames.
    * Output from each invoke of the model needs to be appended to a dataframe and returned as follows:
        .. code-block:: python

            predictions = self.model(frames)
            outcome = pd.DataFrame()
            for prediction in predictions:

                ## YOUR INFERENCE LOGIC

                # column names depend on your implementation
                outcome = outcome.append(
                    {
                        "labels": pred_class,
                        "scores": pred_score,
                        "boxes": pred_boxes
                    },
                    ignore_index=True)

In case you have any other functional requirements (defining custom transformations etc.) you can choose to add more methods. Make sure each method you write is clear, concise and well-documented.

----------

Part 2: Registering and using the UDF in queries
-------

Now that you have implemented your UDF we need to register it in EVA. You can then use the function in any query.

1. Register the UDF with a query that follows this template:

    `CREATE UDF [ IF NOT EXISTS ] <name>
     INPUT  ( [ <arg_name> <arg_data_type> ] [ , ... ] )
     OUTPUT ( [ <result_name> <result_data_type> ] [ , ... ] )
     TYPE  <udf_type_name>
     IMPL  '<path_to_implementation>'`

    where,

        * **<name>** - specifies the unique identifier for the UDF.
        * **[ <arg_name> <arg_data_type> ] [ , ... ]** - specifies the name and data type of the udf input arguments. Name is kept for consistency (ignored by eva right now), arguments data type is required. ANYDIM means the shape is inferred at runtime.
        * **[ <result_name> <result_data_type> ] [ , ... ]** - specifies the name and data type of the udf output arguments. Users can access a specific output of the UDF similar to access a column of a table. Eg. <name>.<result_name>
        * **<udf_type_name>** - specifies the identifier for the type of the UDF. UDFs of the same type are assumed to be interchangeable. They should all have identical input and output arguments. For example, object classification can be one type.
        * **<path_to_implementation>** - specifies the path to the implementation class for the UDF

    Here, is an example query that registers a UDF that wraps around the 'FastRCNNObjectDetector' model that performs Object Detection.

        .. code-block:: sql

            CREATE UDF IF NOT EXISTS FastRCNNObjectDetector
            INPUT  (frame NDARRAY UINT8(3, ANYDIM, ANYDIM))
            OUTPUT (labels NDARRAY STR(ANYDIM), bboxes NDARRAY FLOAT32(ANYDIM, 4),
                    scores NDARRAY FLOAT32(ANYDIM))
            TYPE  Classification
            IMPL  'eva/udfs/fastrcnn_object_detector.py';

    * Input is a frame of type NDARRAY with shape (3, ANYDIM, ANYDIM). 3 channels and any width or height.
    * We return 3 variables for this UDF:
        * `labels`: Predicted label
        * `bboxes`: Bounding box of this object (rectangle coordinates)
        * `scores`: Confidence scores for this prediction

    A status of 0 in the response denotes the successful registration of this UDF.

3. Now you can execute your UDF on any video:

.. code-block:: sql

    SELECT id, Unnest(FastRCNNObjectDetector(data)) FROM MyVideo;

4. You can drop the UDF when you no longer need it.

.. code-block:: sql

    DROP UDF IF EXISTS FastRCNNObjectDetector;
