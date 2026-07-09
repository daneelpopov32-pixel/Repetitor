-- Fix tasks with [null] images by copying from other tasks with same GUID

-- GUID 27F6B8E5F6BA8F314E7D5B96C2EBC83E: copy from 796f0a5e
UPDATE tasks 
SET text_content = text_content::jsonb || '{"images": ["images/60b735e5ea81d0e30b4e544da7000f31.jpg"]}'::jsonb
WHERE id = '13b3907a-abae-4143-ac8b-a17bfc24a2d1';

-- GUID 0D015648BA09A46E4613C0AC2630C55D: copy from 7b6f36c9
UPDATE tasks 
SET text_content = text_content::jsonb || '{"images": ["images/592905b1bc1015b5706b8f311a927cd1.jpg"]}'::jsonb
WHERE id = 'f2eb1fd3-5d60-45cb-a4fe-65ad68ebf1a6';

UPDATE tasks 
SET text_content = text_content::jsonb || '{"images": ["images/592905b1bc1015b5706b8f311a927cd1.jpg"]}'::jsonb
WHERE id = 'bf4b619d-718b-40e0-8357-a441d60909e2';

-- GUID 21A96DD6E011AF184A3004462F0E8D18: copy from 9a6a1212
UPDATE tasks 
SET text_content = text_content::jsonb || '{"images": ["images/592905b1bc1015b5706b8f311a927cd1.jpg"]}'::jsonb
WHERE id = 'fd869bd0-f1b8-4d43-b311-be6c896fac5d';
