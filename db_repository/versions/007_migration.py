from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
post = Table('post', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('header', VARCHAR(length=140)),
    Column('body', TEXT),
    Column('timestamp', TIMESTAMP),
    Column('user_id', INTEGER),
    Column('photo', VARCHAR(length=240)),
    Column('thumbnail', VARCHAR(length=240)),
    Column('slug', VARCHAR(length=255)),
    Column('type', VARCHAR(length=32)),
)

post = Table('post', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('header', String(length=140)),
    Column('body', Text),
    Column('timestamp', DateTime),
    Column('user_id', Integer),
    Column('writing_type', String(length=32)),
    Column('photo', String(length=240)),
    Column('thumbnail', String(length=240)),
    Column('slug', String(length=255)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['post'].columns['type'].drop()
    post_meta.tables['post'].columns['writing_type'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['post'].columns['type'].create()
    post_meta.tables['post'].columns['writing_type'].drop()
