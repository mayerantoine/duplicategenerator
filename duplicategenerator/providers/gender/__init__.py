from .. import BaseProvider
from collections import OrderedDict

class GenderProvider(BaseProvider):
    """ Gender Provider class
    """    
    
    def gender(self):
        return self.random_element(
            OrderedDict([
        ('Male',0.4),
        ('Female',0.6)
    ]))
