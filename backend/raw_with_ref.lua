
-- # Copyright (C) 2021 Humanitarian OpenStreetmap Team

-- # This program is free software: you can redistribute it and/or modify
-- # it under the terms of the GNU Affero General Public License as
-- # published by the Free Software Foundation, either version 3 of the
-- # License, or (at your option) any later version.

-- # This program is distributed in the hope that it will be useful,
-- # but WITHOUT ANY WARRANTY; without even the implied warranty of
-- # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- # GNU Affero General Public License for more details.

-- # You should have received a copy of the GNU Affero General Public License
-- # along with this program.  If not, see <https://www.gnu.org/licenses/>.

-- # Humanitarian OpenStreetmap Team
-- # 1100 13th Street NW Suite 800 Washington, D.C. 20005
-- # <info@hotosm.org>
-- This is lua script for osm2pgsql in order to create and process custom schema to store incoming osm data efficiently

-- osm2pgsql --create -H localhost -U admin -P 5432 -d postgres -W --extra-attributes --output=flex --style ./raw.lua nepal-latest-internal.osm.pbf 


-- Set projection to 4326 
local srid = 4326

local tables = {}

tables.nodes = osm2pgsql.define_table{
    name="nodes", 
    -- This will generate a derived nodes table which stores all the nodes feature with their point geometry 
    ids = {type='node',id_column = 'osm_id' },
    columns = {
        { column = 'uid', type = 'int' },
        { column = 'user', type = 'text' },
        { column = 'version', type = 'int' },
        { column = 'changeset', type = 'int' },
        { column = 'timestamp', sql_type = 'timestamp' },
        { column = 'tags', type = 'jsonb' },
        { column = 'geom', type = 'point', projection = srid },
        { column = 'country', sql_type= 'int[]', create_only = true },
        
    }

}

tables.ways_line = osm2pgsql.define_table{
    name="ways_line", 
    -- This will generate a derived ways line table which stores all the ways feature with linestring geometry 
    ids = {type='way',id_column = 'osm_id' },
    columns = {
        { column = 'uid', type = 'int' },
        { column = 'user', type = 'text' },
        { column = 'version', type = 'int' },
        { column = 'changeset', type = 'int' },
        { column = 'timestamp', sql_type = 'timestamp' },
        { column = 'tags', type = 'jsonb' },
        { column = 'refs', type= 'text', sql_type = 'bigint[]'},
        { column = 'geom', type = 'linestring', projection = srid },
        { column = 'country', sql_type= 'int[]', create_only = true },

    }

}

tables.ways_poly = osm2pgsql.define_table{
    name="ways_poly", 
    -- This will generate a derived ways poly table which stores all the ways feature with polygon geometry 
    ids = {type='way',id_column = 'osm_id' },
    columns = {
        { column = 'uid', type = 'int' },
        { column = 'user', type = 'text' },
        { column = 'version', type = 'int' },
        { column = 'changeset', type = 'int' },
        { column = 'timestamp', sql_type = 'timestamp' },
    -- This will store tags as jsonb type  
        { column = 'tags', type = 'jsonb' },
        { column = 'refs', type= 'text', sql_type = 'bigint[]'},
        { column = 'geom', type = 'polygon', projection = srid },
        { column = 'grid', type = 'int', create_only = true },
        { column = 'country', sql_type= 'int[]', create_only = true },
    }

}

tables.rels = osm2pgsql.define_table{
    name="relations", 
    -- This will generate a derived realtion  table which stores all the relation feature to query without storing meta data parts and members

    ids = {type='relation', id_column = 'osm_id' },
    columns = {

        { column = 'uid', type = 'int' },
        { column = 'user', type = 'text' },
        { column = 'version', type = 'int' },
        { column = 'changeset', type = 'int' },
        { column = 'timestamp', sql_type = 'timestamp' },
        { column = 'tags', type = 'jsonb' },
        { column = 'refs', type = 'jsonb'},
        { column = 'geom', type = 'geometry', projection = srid },
        { column = 'country',sql_type= 'int[]', create_only = true },
        
    }
}

-- Returns true if there are no tags left.
function clean_tags(tags)
    tags.odbl = nil
    -- tags.created_by = nil
    tags['source:ref'] = nil
    return next(tags) == nil
end

function osm2pgsql.process_node(object)

    if clean_tags(object.tags) then
        return
    end

    tables.nodes:add_row({
        uid = object.uid,
        user = object.user,
        version = object.version,
        changeset = object.changeset,
        timestamp = os.date('!%Y-%m-%dT%H:%M:%SZ', object.timestamp),
        tags = object.tags,
        geom = { create = 'point' }
    })
end

function osm2pgsql.process_way(object)
    if clean_tags(object.tags) then
        return
    end
 
    if object.is_closed and #object.nodes>3 then
        tables.ways_poly:add_row({
            uid = object.uid,
            user = object.user,
            version = object.version,
            changeset = object.changeset,
            timestamp = os.date('!%Y-%m-%dT%H:%M:%SZ', object.timestamp),
            tags = object.tags,
            refs = '{' .. table.concat(object.nodes, ',') .. '}',
            geom = { create = 'area' },
            
        })
    else
        tables.ways_line:add_row({
            uid = object.uid,
            user = object.user,
            version = object.version,
            changeset = object.changeset,
            timestamp = os.date('!%Y-%m-%dT%H:%M:%SZ', object.timestamp),
            tags = object.tags,
            refs = '{' .. table.concat(object.nodes, ',') .. '}',
            geom = { create = 'line' },
            
        })
    end
end

function osm2pgsql.process_relation(object)
    if clean_tags(object.tags) then
        return
    end
    if object.tags.type == 'multipolygon' or object.tags.type == 'boundary' then
        tables.rels:add_row({
            uid = object.uid,
            user = object.user,
            version = object.version,
            changeset = object.changeset,
            timestamp = os.date('!%Y-%m-%dT%H:%M:%SZ', object.timestamp),
            tags = object.tags,
            geom = { create = 'area' },
            refs = object.members

        })
    else
        tables.rels:add_row({
            uid = object.uid,
            user = object.user,
            version = object.version,
            changeset = object.changeset,
            timestamp = os.date('!%Y-%m-%dT%H:%M:%SZ', object.timestamp),
            tags = object.tags,
            geom= { create = 'line' },
            refs = object.members

        })
    end
end

