-- Comprehensive fix script for wagtailsearch_indexentry table
-- Run with: docker compose exec db psql -U postgres -d portfolio_strategist -f fix_wagtailsearch.sql
-- Or copy-paste these commands into an interactive psql session

-- Verify table exists
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = 'wagtailsearch_indexentry'
) as table_exists;

-- Check current table structure
\d wagtailsearch_indexentry

-- Ensure all columns exist with correct types
DO $$
BEGIN
    -- Add autocomplete column if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'wagtailsearch_indexentry' 
        AND column_name = 'autocomplete'
    ) THEN
        ALTER TABLE wagtailsearch_indexentry 
        ADD COLUMN autocomplete tsvector NOT NULL DEFAULT '';
    END IF;

    -- Add title column if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'wagtailsearch_indexentry' 
        AND column_name = 'title'
    ) THEN
        ALTER TABLE wagtailsearch_indexentry 
        ADD COLUMN title tsvector NOT NULL DEFAULT '';
    END IF;

    -- Add body column if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'wagtailsearch_indexentry' 
        AND column_name = 'body'
    ) THEN
        ALTER TABLE wagtailsearch_indexentry 
        ADD COLUMN body tsvector NOT NULL DEFAULT '';
    END IF;
END
$$;

-- Ensure unique constraint exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'wagtailsearch_indexentry_content_type_id_object_i_bcd7ba73_uniq'
    ) THEN
        ALTER TABLE wagtailsearch_indexentry 
        ADD CONSTRAINT wagtailsearch_indexentry_content_type_id_object_i_bcd7ba73_uniq 
        UNIQUE (content_type_id, object_id);
    END IF;
END
$$;

-- Ensure foreign key constraint exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'wagtailsearch_indexe_content_type_id_62ed694f_fk_django_co'
    ) THEN
        ALTER TABLE wagtailsearch_indexentry 
        ADD CONSTRAINT wagtailsearch_indexe_content_type_id_62ed694f_fk_django_co 
        FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) 
        DEFERRABLE INITIALLY DEFERRED;
    END IF;
END
$$;

-- Ensure all indexes exist
CREATE INDEX IF NOT EXISTS wagtailsearch_indexentry_content_type_id_62ed694f 
    ON wagtailsearch_indexentry (content_type_id);

CREATE INDEX IF NOT EXISTS wagtailsear_autocom_476c89_gin 
    ON wagtailsearch_indexentry USING gin (autocomplete);

CREATE INDEX IF NOT EXISTS wagtailsear_title_9caae0_gin 
    ON wagtailsearch_indexentry USING gin (title);

CREATE INDEX IF NOT EXISTS wagtailsear_body_90c85d_gin 
    ON wagtailsearch_indexentry USING gin (body);

-- Verify final state
SELECT 
    'Table structure verified' as status,
    COUNT(*) as row_count
FROM wagtailsearch_indexentry;

-- List all indexes
SELECT 
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'wagtailsearch_indexentry';

