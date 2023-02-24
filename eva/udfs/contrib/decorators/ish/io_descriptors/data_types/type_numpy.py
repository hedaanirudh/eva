from eva.udfs.contrib.decorators.ish.io_descriptors.eva_arguments import EvaArgument
import numpy as np

class NumpyArray(EvaArgument):
    
    def __init__(self, shape = None, dtype = None) -> None:
        super().__init__()
        self.shape = shape
        self.dtype = dtype
        
    def check_type(self, input_object) -> bool:
        if self.dtype:
            if self.dtype == "int32":
                return (isinstance(input_object, np.ndarray) and (input_object.dtype == np.int32))
            elif self.dtype == "float16":
                return (isinstance(input_object, np.ndarray) and (input_object.dtype == np.float16))
            elif self.dtype == "float32":
                return (isinstance(input_object, np.ndarray) and (input_object.dtype == np.float32))
            
        else:
            return isinstance(input_object, np.ndarray)

    
    def check_shape(self, input_object) -> bool:
        if self.shape:
            if input_object.shape != self.shape:
                return False
            
        return True
    
            
    
    def name(self):
        return "NumpyArray"
        
        


    