###################################
## Driftwood 2D Game Dev. Suite  ##
## entitymanager.py              ##
## Copyright 2014 PariahSoft LLC ##
###################################

## **********
## Permission is hereby granted, free of charge, to any person obtaining a copy
## of this software and associated documentation files (the "Software"), to
## deal in the Software without restriction, including without limitation the
## rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
## sell copies of the Software, and to permit persons to whom the Software is
## furnished to do so, subject to the following conditions:
##
## The above copyright notice and this permission notice shall be included in
## all copies or substantial portions of the Software.
##
## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
## IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
## FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
## AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
## LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
## FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
## IN THE SOFTWARE.
## **********

import entity
from inputmanager import InputManager


class EntityManager:
    """The Entity Manager

    This class manages entities in the current area, as well as the persistent player entity.

    Attributes:
        driftwood: Base class instance.

        player: The player entity.
        collider: The collision callback. The callback must take as arguments the two entities that collided.

        entities: The list of Entity class instances for each entity.
        spritesheets: The list of Spritesheet class instances for each sprite sheet.
    """
    def __init__(self, driftwood):
        """EntityManager class initializer.

        Args:
            driftwood: Base class instance.
        """
        self.driftwood = driftwood

        self.player = None
        self.collider = None

        self.entities = []

        self.spritesheets = []

        self.__last_eid = -1

    def insert(self, filename, layer, x, y):
        """Insert an entity at a position in the area.

        Args:
            filename: Filename of the JSON entity descriptor.
            layer: Layer of insertion.
            x: x-coordinate of insertion.
            y: y-coordinate of insertion.

        Returns: New entity if succeeded, None if failed.
        """
        data = self.driftwood.resource.request_json(filename)

        if data["mode"] == "tile":
            self.entities.append(entity.TileModeEntity(self))

        elif data["mode"] == "pixel":
            self.entities.append(entity.PixelModeEntity(self))

        else:
            self.driftwood.log.msg("ERROR", "Entity", "invalid mode", "\"{0}\"".format(data["mode"]))
            return None

        self.__last_eid += 1
        eid = self.__last_eid

        self.entities[eid]._read(filename, eid)

        self.entities[eid].x = x
        self.entities[eid].y = y
        self.entities[eid].layer = layer

        # Are we on a tile?
        if (x % self.driftwood.area.tilemap.tilewidth == 0) and (y % self.driftwood.area.tilemap.tileheight == 0):
            self.entities[eid].tile = self.driftwood.area.tilemap.layers[layer].tile(
                x / self.driftwood.area.tilemap.tilewidth,
                y / self.driftwood.area.tilemap.tileheight
            )

        else:
            self.driftwood.log.msg("ERROR", "Entity", "must start on a tile")
            return None

        self.driftwood.area.changed = True

        self.driftwood.log.info("Entity", "inserted", "{0} entity on layer {1} at position {2}, {3}".format(filename,
                                                                                                            layer,
                                                                                                            x, y))

        if "on_insert" in data:
            args = data["on_insert"].split(':')
            self.driftwood.script.call(args[0], args[1], self.entities[eid])

        return self.entities[-1]

    def entity(self, eid):
        """Retrieve an entity by eid

        Args:
            eid: The Entity ID of the entity to retrieve.

        Returns: Entity class instance.
        """
        for ent in self.entities:
            if ent.eid == eid:
                return ent

    def layer(self, layer):
        """Retrieve a list of entities on a certain layer.

        Args:
            layer: Layer to find entities on.

        Returns: Tuple of Entity class instances.
        """
        ents = []

        for ent in self.entities:
            if ent.layer == layer:
                ents.append(ent)

        return tuple(ents)

    def kill(self, eid):
        """Kill an entity by eid.

        Args:
            eid: The Entity ID of the entity to kill.
        """
        for ent in range(len(self.entities)):
            if self.entities[ent].eid == eid:
                del self.entities[ent]

        self.driftwood.area.changed = True

    def killall(self, filename):
        """Kill all entities by filename.

        Args:
            filename: Filename of the JSON entity descriptor whose insertions should be killed.
        """
        for ent in range(len(self.entities)):
            if self.entities[ent].filename == filename:
                del self.entities[ent]

        self.driftwood.area.changed = True

    def spritesheet(self, filename):
        """Retrieve a sprite sheet by its filename.

        Args:
            filename: Filename of the sprite sheet image.

        Returns: Spritesheet class instance.
        """
        for ss in self.spritesheets:
            if ss.filename == filename:
                return ss

    def collision(self, a, b):
        """Notify the collision callback, if set, that entity "a" has collided with entity or tile "b".

        Args:
            a: First colliding entity.
            b: Second colliding entity or tile.
        """
        if self.collider:
            self.collider(a, b)

    def setup_player(self, ent):
        """Helper function to setup an entity as a functional player.

        Sets the player and its default keybindings.

        Args:
            ent: Entity to become the player
        """

        self.player = ent

        getkey = lambda keyid: getattr(self.driftwood.keycode,
                                       self.driftwood.config["input"]["keybindings"][keyid])

        self.driftwood.input.register(getkey("up"), self.__default_keybind_move(0, -1))
        self.driftwood.input.register(getkey("down"), self.__default_keybind_move(0, 1))
        self.driftwood.input.register(getkey("left"), self.__default_keybind_move(-1, 0))
        self.driftwood.input.register(getkey("right"), self.__default_keybind_move(1, 0))

    def __default_keybind_move(self, x, y):
        def move(keyevent):
            player = self.driftwood.entity.player
            if keyevent == InputManager.ONDOWN:
                player.set_next_velocity(x, y)
            elif keyevent == InputManager.ONREPEAT:
                # Handle key released but a second one from earlier still held down.
                player.set_next_velocity(x, y)
            elif keyevent == InputManager.ONUP:
                player.set_next_velocity(0, 0)
        return move
