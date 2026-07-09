UPDATE tasks 
SET text_content = text_content::jsonb || '{"images": ["images/705c9f82048ee08ac3527bbf3d7ca70e.jpg"]}'::jsonb
WHERE id = '3443603a-45ad-41ff-9d2d-e0777bbc9116';
