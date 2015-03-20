from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
comment = Table('comment', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('body', VARCHAR(length=500)),
    Column('created_at', DATETIME),
    Column('post', INTEGER),
    Column('user', INTEGER),
)

comment = Table('comment', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('body', String(length=500)),
    Column('post_id', Integer),
    Column('user_id', Integer),
    Column('created_at', DateTime),
)

post = Table('post', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('body', VARCHAR(length=140)),
    Column('timestamp', DATETIME),
    Column('language', VARCHAR(length=5)),
    Column('photo', VARCHAR(length=240)),
    Column('slug', VARCHAR(length=255)),
    Column('user', INTEGER),
)

post = Table('post', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('body', String(length=140)),
    Column('timestamp', DateTime),
    Column('user_id', Integer),
    Column('language', String(length=5)),
    Column('photo', String(length=240)),
    Column('slug', String(length=255)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['comment'].columns['post'].drop()
    pre_meta.tables['comment'].columns['user'].drop()
    post_meta.tables['comment'].columns['post_id'].create()
    post_meta.tables['comment'].columns['user_id'].create()
    pre_meta.tables['post'].columns['user'].drop()
    post_meta.tables['post'].columns['user_id'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['comment'].columns['post'].create()
    pre_meta.tables['comment'].columns['user'].create()
    post_meta.tables['comment'].columns['post_id'].drop()
    post_meta.tables['comment'].columns['user_id'].drop()
    pre_meta.tables['post'].columns['user'].create()
    post_meta.tables['post'].columns['user_id'].drop()
