class Vehicle(object):
    """
    Vehicle class
    """
    model = 'vehicle.lincoln.mkz2017'
    rolename = 'hero'
    transform = None
    color = None
    category = None

    def __init__(self, model, rolename, transform):
        self.model = model
        self.rolename = rolename
        self.transform = transform