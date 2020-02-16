import models
import news_loader

class MockClassifier:
    def __init__(self, named_entitiles=None):
        self.named_entitiles = named_entitiles

    def get_named_entities(self, text):
        return self.named_entitiles


def test_match_event_for_news():
    news = models.News(headline="Donald Trump")
    classifier = MockClassifier(named_entitiles=['Donald', 'Trump'])
    events = [models.Event(id=1, keywords={'Trump'})]

    event = news_loader.match_event(news, events, classifier)
    assert event == events[0]

