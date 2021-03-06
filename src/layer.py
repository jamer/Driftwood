###################################
## Driftwood 2D Game Dev. Suite  ##
## layer.py                      ##
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

import tile


class Layer:
    """This class abstracts a layer.

    Attributes:
        tilemap: Parent Tilemap instance.

        properties: A dictionary containing layer properties.

        tiles: The list of Tile class instances for each tile.
    """
    def __init__(self, tilemap, layerdata, zpos):
        """Layer class initializer.

        Args:
            tilemap: Link back to the parent Tilemap instance.
            layerdata: JSON layer segment.
            zpos: Layer's z-position.
        """
        self.tilemap = tilemap

        self.zpos = zpos
        self.properties = {}

        self.tiles = []

        # This contains the JSON of the layer.
        self.__layer = layerdata

        self.__prepare_layer()

    def __prepare_layer(self):
        # Set layer properties if present.
        if "properties" in self.__layer:
            self.properties = self.__layer["properties"]

        # Iterate through the tile graphic IDs.
        for seq, gid in enumerate(self.__layer["data"]):
            # Does this tile actually exist?
            if gid:
                # Find which tileset the tile's graphic is in.
                for ts in self.tilemap.tilesets:
                    if gid in range(*ts.range):
                        # Create the Tile instance for this tile.
                        self.tiles.append(tile.Tile(self, seq, ts, gid))

            # No tile, here create a dummy tile.
            else:
                self.tiles.append(tile.Tile(self, seq, None, None))

    def _process_objects(self, objdata):
        """Process and merge an object layer into the tile layer below.

        This method is marked private even though it's called from Tilemap, because it should not be called outside the
        engine code.

        Args:
            objdata: JSON object layer segment.
        """
        if "properties" in objdata:
            self.properties.update(objdata["properties"])

        for obj in objdata["objects"]:
            # Is the object properly sized?
            if (obj["x"] % self.tilemap.tilewidth or obj["y"] % self.tilemap.tileheight or
                    obj["width"] % self.tilemap.tilewidth or obj["height"] % self.tilemap.tileheight):
                self.tilemap.area.driftwood.log.msg("ERROR", "Map", "invalid object size or placement")
                continue

            # Map object properties onto their tiles.
            for x in range(0, obj["width"] // self.tilemap.tilewidth):
                for y in range(0, obj["height"] // self.tilemap.tileheight):
                    tx = obj["x"] // self.tilemap.tilewidth + x
                    ty = obj["y"] // self.tilemap.tileheight + y

                    # Insert the object properties.
                    self.tile(tx, ty).properties.update(obj["properties"])

                    # Set nowalk if present.
                    if "nowalk" in self.tile(tx, ty).properties:
                        self.tile(tx, ty).nowalk = self.tile(tx, ty).properties["nowalk"]

                    # Set exit if present.
                    for exittype in ["exit", "exit:up", "exit:down", "exit:left", "exit:right"]:
                        if exittype in self.tile(tx, ty).properties:
                            self.tile(tx, ty).exits[exittype] = self.tile(tx, ty).properties[exittype]

            # TODO: Handle entity spawns on object type "entity".
            if obj["type"] == "entity":
                pass

    def tile(self, x, y):
        """Retrieve a tile from the layer by its coordinates.

        Args:
            x: x-coordinate
            y: y-coordinate

        Returns: Tile instance or None if out of bounds.
        """
        if x < 0 or y < 0 or x >= self.tilemap.width or y >= self.tilemap.height:
            return None

        try:
            t = self.tiles[int((y * self.tilemap.width) + x)]
            return t

        except IndexError:
            return None
