from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
comment = Table('comment', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('body', VARCHAR(length=500)),
    Column('post_id', INTEGER),
    Column('created_at', DATETIME),
)

comment = Table('comment', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('body', String(length=500)),
    Column('post', Integer),
    Column('user', Integer),
    Column('created_at', DateTime),
)

post = Table('post', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('body', VARCHAR(length=140)),
    Column('timestamp', DATETIME),
    Column('user_id', INTEGER),
    Column('language', VARCHAR(length=5)),
    Column('photo', VARCHAR(length=240)),
    Column('slug', VARCHAR(length=255)),
)

post = Table('post', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('body', String(length=140)),
    Column('timestamp', DateTime),
    Column('user', Integer),
    Column('language', String(length=5)),
    Column('photo', String(length=240)),
    Column('slug', String(length=255)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['comment'].columns['post_id'].drop()
    post_meta.tables['comment'].columns['post'].create()
    post_meta.tables['comment'].columns['user'].create()
    pre_meta.tables['post'].columns['user_id'].drop()
    post_meta.tables['post'].columns['user'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['comment'].columns['post_id'].create()
    post_meta.tables['comment'].columns['post'].drop()
    post_meta.tables['comment'].columns['user'].drop()
    pre_meta.tables['post'].columns['user_id'].create()
    post_meta.tables['post'].columns['user'].drop()
