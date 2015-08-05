import re
from haystack import indexes
from .models import Asset, Collection

class FieldPreparersMixin:
    '''
    Haystack uses commas as separators for MultiValueField:
    https://github.com/django-haystack/django-haystack/blob/v2.4.0/haystack/backends/whoosh_backend.py#L159
    We'll find commas (and spaces, to mimic Gmail) and replace them with dashes.
    '''
    COMMA_SPACE_RE = re.compile('[, ]')
    def _escape_comma_space(self, string, repl='-'):
        return re.sub(self.COMMA_SPACE_RE, repl, string) 

    def prepare_tag(self, obj):
        return [
            self._escape_comma_space(t.name)
            for t in obj.tags.all()
        ]
    def prepare_name__exact(self, obj):
        return self._escape_comma_space(obj.name)
    def prepare_asset_type(self, obj):
        return self._escape_comma_space(obj.asset_type)
    def prepare_owner__username__exact(self, obj):
        if obj.owner:
            return self._escape_comma_space(obj.owner.username)
        else:
            return None
    def prepare_parent__name__exact(self, obj):
        if obj.parent:
            return self._escape_comma_space(obj.parent.name)
        else:
            return None

class AssetIndex(indexes.SearchIndex, indexes.Indexable, FieldPreparersMixin):
    # Haystack usually doesn't deal well with double underscores in field names
    # (searches fail silently when Haystack's split_expression() throws away
    # everything after the double underscores), but we can get away with it
    # since our queries use Raw().
    text = indexes.CharField(document=True, use_template=True)
    name = indexes.CharField(model_attr='name')
    owner__username = indexes.CharField(model_attr='owner__username', null=True)
    parent__name = indexes.CharField(model_attr='parent__name', null=True)
    tag = indexes.MultiValueField()
    # There's nothing multi-valued about these fields, but using
    # MultiValueField convinces Haystack to use Whoosh's KEYWORD field, which
    # in turn uses KeywordAnalyzer. Then, by replacing commas, we can force the
    # entire field to be a single token. This would be much easier if Haystack
    # allowed us to use Whoosh's ID field.
    name__exact = indexes.MultiValueField()
    asset_type = indexes.MultiValueField()
    owner__username__exact = indexes.MultiValueField()
    parent__name__exact = indexes.MultiValueField()
    def get_model(self):
        return Asset

class CollectionIndex(indexes.SearchIndex, indexes.Indexable, FieldPreparersMixin):
    # Haystack seems allergic to mixins and inheritance (even from ABCs!),
    # so throw DRY to the wind
    text = indexes.CharField(document=True, use_template=True)
    name = indexes.CharField(model_attr='name')
    owner__username = indexes.CharField(model_attr='owner__username')
    parent__name = indexes.CharField(model_attr='parent__name', null=True)
    tag = indexes.MultiValueField()
    # Not really multi-valued; see AssetIndex for explanation
    name__exact = indexes.MultiValueField()
    owner__username__exact = indexes.MultiValueField()
    parent__name__exact = indexes.MultiValueField()
    def get_model(self):
        return Collection