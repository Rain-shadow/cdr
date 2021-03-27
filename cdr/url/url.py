import cdr.request as requests

resource = {
    "main": [
        "https://app.vocabgo.com/overall/#/student/home",
        "https://app.vocabgo.com/overall/js/app.c93fe9bc.js",
        "https://app.vocabgo.com/overall/js/chunk-vendors.6e6d49d5.js",
        "https://app.vocabgo.com/overall/js/chunk-2d0d2f1f.911d2b7f.js",
        "https://app.vocabgo.com/student/#/student/home",
        "https://app.vocabgo.com/overall/favicon.ico",
        "https://app.vocabgo.com/student/css/app.1.210301.2.1614587768011.css?v=1.210301.2",
        "https://app.vocabgo.com/student/css/chunk-vendors.1.210301.2.1614587768011.css?v=1.210301.2",
        "https://app.vocabgo.com/student/viewport-units-buggyfill.js",
        "https://app.vocabgo.com/student/js/app.1.210301.2.1614587768011.js?v=1.210301.2",
        "https://app.vocabgo.com/student/js/chunk-vendors.1.210301.2.1614587768011.js?v=1.210301.2",
        "https://app.vocabgo.com/student/favicon.ico",
    ],
    "myself_task_list": [
        "https://app.vocabgo.com/student/css/chunk-086abba0.1.210301.2.1614587768011.css?v=1.210301.2",
        "https://app.vocabgo.com/student/js/chunk-086abba0.1.210301.2.1614587768011.js?v=1.210301.2",
        "https://app.vocabgo.com/student/css/chunk-187cc57f.1.210301.2.1614587768011.css?v=1.210301.2",
        "https://app.vocabgo.com/student/css/chunk-a387e506.1.210301.2.1614587768011.css?v=1.210301.2",
        "https://app.vocabgo.com/student/js/chunk-187cc57f.1.210301.2.1614587768011.js?v=1.210301.2",
        "https://app.vocabgo.com/student/js/chunk-a387e506.1.210301.2.1614587768011.js?v=1.210301.2",
    ],
    "task_detail": [
        "https://app.vocabgo.com/student/css/chunk-827b705c.1.210301.2.1614587768011.css?v=1.210301.2",
        "https://app.vocabgo.com/student/js/chunk-827b705c.1.210301.2.1614587768011.js?v=1.210301.2",
        "https://app.vocabgo.com/student/css/chunk-9eeec03e.1.210301.2.1614587768011.css?v=1.210301.2",
        "https://app.vocabgo.com/student/js/chunk-9eeec03e.1.210301.2.1614587768011.js?v=1.210301.2",
        "https://app.vocabgo.com/student/css/chunk-72567464.1.210301.2.1614587768011.css?v=1.210301.2",
        "https://app.vocabgo.com/student/js/chunk-72567464.1.210301.2.1614587768011.js?v=1.210301.2",
        "https://app.vocabgo.com/student/css/chunk-2349fe8c.1.210301.2.1614587768011.css?v=1.210301.2",
        "https://app.vocabgo.com/student/js/chunk-2349fe8c.1.210301.2.1614587768011.js?v=1.210301.2",
    ],
    "choose_word": [
        "https://app.vocabgo.com/student/css/chunk-49a4e238.1.210301.2.1614587768011.css?v=1.210301.2",
        "https://app.vocabgo.com/student/css/chunk-442dab5f.1.210301.2.1614587768011.css?v=1.210301.2",
        "https://app.vocabgo.com/student/css/chunk-2e834b0a.1.210301.2.1614587768011.css?v=1.210301.2",
        "https://app.vocabgo.com/student/js/chunk-49a4e238.1.210301.2.1614587768011.js?v=1.210301.2",
        "https://app.vocabgo.com/student/js/chunk-442dab5f.1.210301.2.1614587768011.js?v=1.210301.2",
        "https://app.vocabgo.com/student/js/chunk-2e834b0a.1.210301.2.1614587768011.js?v=1.210301.2",
    ]
}


class URL:

    @staticmethod
    def load_main():
        global resource
        URL.__load_resource(resource["main"])

    @staticmethod
    def load_myself_task_list():
        global resource
        URL.__load_resource(resource["myself_task_list"])

    @staticmethod
    def load_task_detail():
        global resource
        URL.__load_resource(resource["task_detail"])

    @staticmethod
    def load_choose_word():
        global resource
        URL.__load_resource(resource["choose_word"])

    @staticmethod
    def __load_resource(resources: list):
        for url in resources:
            requests.get(url).close()
