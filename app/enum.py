from enum import Enum

DEFAULT = 0
COMMENT = 1
SEARCH = 2


class DictEnum(Enum):
    USER1: list = ['user_id', 'user_name', 'avatar']
    USER2: list = ['user_id', 'user_account', 'user_name', 'avatar', 'description', 'is_admin', 'fans_num', 'video_num',
                   'follow_num']
    VIDEO2: list = ['video_id', 'title', 'thumbnail', 'url', 'video_view', 'video_like', 'video_favorite',
                    'video_comment', 'publisher', 'publish_date', 'duration']
    COMMENT1: list = ['comment_id', 'user', 'comment_content', 'comment_date', 'edited']
    COMMENTCOMMENT1: list = ['comment_comment_id', 'user', 'reply_to_user',
                             'comment_comment_content', 'comment_comment_date', 'edited']
