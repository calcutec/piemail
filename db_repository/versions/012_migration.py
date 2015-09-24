from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
poem = Table('poem', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('author', VARCHAR),
    Column('title', VARCHAR),
    Column('body', TEXT),
    Column('slug', VARCHAR),
    Column('writing_type', VARCHAR(length=32)),
    Column('votes', INTEGER),
)

user = Table('user', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('type', Integer),
    Column('firstname', String(length=100)),
    Column('lastname', String(length=100)),
    Column('nickname', String(length=64)),
    Column('email', String(length=120)),
    Column('pwdhash', String(length=100)),
    Column('about_me', String(length=140)),
    Column('profile_photo', String(length=240)),
    Column('thumbnail', String(length=240)),
    Column('last_seen', DateTime),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['poem'].drop()
    post_meta.tables['user'].columns['thumbnail'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['poem'].create()
    post_meta.tables['user'].columns['thumbnail'].drop()
