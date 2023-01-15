# ==============================================================================
# -- GnssSensor ----------------------------------------------------------------
# ==============================================================================

import carla
import weakref

class GnssSensor(object):
    def __init__(self, parent_actor, transform = None, sensor_options = {}):
        if transform is None:
            transform = carla.Transform(carla.Location(x=1.0, z=2.8))

        self.sensor = None
        self._parent = parent_actor
        self.lat = 0.0
        self.lon = 0.0
        world = self._parent.get_world()
        bp = world.get_blueprint_library().find('sensor.other.gnss')

        for key in sensor_options:
            bp.set_attribute(key, sensor_options[key])

        self.sensor = world.spawn_actor(bp, transform, attach_to=self._parent)
        # We need to pass the lambda a weak reference to self to avoid circular
        # reference.
        weak_self = weakref.ref(self)
        self.sensor.listen(lambda event: GnssSensor._on_gnss_event(weak_self, event))

    @staticmethod
    def _on_gnss_event(weak_self, event):
        self = weak_self()
        if not self:
            return
        self.lat = event.latitude
        self.lon = event.longitude
    
    def stop(self):
        self.sensor.stop()

    def destroy(self):
        self.sensor.destroy()