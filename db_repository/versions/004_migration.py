from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
post = Table('post', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('header', String(length=140)),
    Column('body', Text),
    Column('timestamp', DateTime),
    Column('user_id', Integer),
    Column('language', String(length=5)),
    Column('type', String(length=32)),
    Column('photo', String(length=240)),
    Column('thumbnail', String(length=240)),
    Column('slug', String(length=255)),
)

user = Table('user', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('social_id', VARCHAR(length=64)),
    Column('firstname', VARCHAR(length=100)),
    Column('lastname', VARCHAR(length=100)),
    Column('nickname', VARCHAR(length=64)),
    Column('email', VARCHAR(length=120)),
    Column('pwdhash', VARCHAR(length=100)),
    Column('about_me', VARCHAR(length=140)),
    Column('profile_photo', VARCHAR(length=240)),
    Column('last_seen', TIMESTAMP),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['post'].columns['type'].create()
    pre_meta.tables['user'].columns['social_id'].drop()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['post'].columns['type'].drop()
    pre_meta.tables['user'].columns['social_id'].create()
