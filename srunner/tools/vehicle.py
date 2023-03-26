import carla

class Vehicle(object):
    """
    Vehicle class
    """
    def __init__(self, 
                 model='vehicle.lincoln.mkz2017', 
                 rolename='hero', 
                 transform=carla.Transform(), 
                 color=None, 
                 category="car"):
        self.model = model
        self.rolename = rolename
        self.transform = transform
        self.color = color
        self.category = category