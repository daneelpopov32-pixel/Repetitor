-- Deduplicate tasks by GUID: keep only the best copy per GUID
-- Order: answers -> test_tasks -> tasks

-- Step 1: Create temp table with IDs to KEEP (best copy per GUID)
CREATE TEMPORARY TABLE keep_ids AS
SELECT DISTINCT ON (metadata->>'fipi_guid')
  id
FROM tasks
WHERE metadata->>'fipi_guid' IS NOT NULL AND metadata->>'fipi_guid' != ''
ORDER BY 
  metadata->>'fipi_guid',
  (CASE WHEN (text_content->>'images') IS NOT NULL AND (text_content->>'images') != 'null' AND (text_content->>'images') != '[null]' AND length(text_content->>'images') > 2 THEN 0 ELSE 1 END),
  (CASE WHEN (text_content->>'fipi_urls') IS NOT NULL AND length(text_content->>'fipi_urls') > 2 THEN 0 ELSE 1 END),
  id;

-- Step 2: Show what we're deleting
SELECT 'Duplicate tasks to delete' as info,
       COUNT(*) as count
FROM tasks
WHERE metadata->>'fipi_guid' IS NOT NULL AND metadata->>'fipi_guid' != ''
  AND id NOT IN (SELECT id FROM keep_ids);

-- Step 3: Delete answers referencing duplicate tasks
DELETE FROM answers WHERE task_id IN (
  SELECT id FROM tasks
  WHERE metadata->>'fipi_guid' IS NOT NULL AND metadata->>'fipi_guid' != ''
    AND id NOT IN (SELECT id FROM keep_ids)
);

-- Step 4: Delete test_tasks referencing duplicate tasks
DELETE FROM test_tasks WHERE task_id IN (
  SELECT id FROM tasks
  WHERE metadata->>'fipi_guid' IS NOT NULL AND metadata->>'fipi_guid' != ''
    AND id NOT IN (SELECT id FROM keep_ids)
);

-- Step 5: Delete the duplicate task rows
DELETE FROM tasks
WHERE metadata->>'fipi_guid' IS NOT NULL AND metadata->>'fipi_guid' != ''
  AND id NOT IN (SELECT id FROM keep_ids);

-- Cleanup
DROP TABLE keep_ids;

-- Step 6: Verify
SELECT 'After dedup' as status,
       COUNT(*) as total_tasks,
       SUM(CASE WHEN metadata->>'fipi_guid' IS NOT NULL AND metadata->>'fipi_guid' != '' THEN 1 ELSE 0 END) as with_guid,
       SUM(CASE WHEN (text_content->>'images') IS NOT NULL AND (text_content->>'images') != 'null' AND (text_content->>'images') != '[null]' AND length(text_content->>'images') > 2 THEN 1 ELSE 0 END) as with_images
FROM tasks;
