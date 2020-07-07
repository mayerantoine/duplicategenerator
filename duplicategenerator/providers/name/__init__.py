from .. import BaseProvider

localized = True

class NameProvider(BaseProvider):
    
    surnames = ('Doe','Antoine')
    
    def surname(self):
        return self.random_element(self.surnames)
    
    def given_name(self):
        return self.random_element(self.given_name)