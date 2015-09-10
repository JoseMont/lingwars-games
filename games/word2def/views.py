
from django.conf import settings
from django.core.urlresolvers import reverse

from engine.utils.views import QuestionView
from engine.utils.game import QuestionError

from .models import Question, Definition

ACCESS_TOKEN_IO = getattr(settings, 'ACCESS_TOKEN_IO')
ACCESS_TOKEN_STORE = getattr(settings, 'ACCESS_TOKEN_STORE')


class Word2DefQuestionView(QuestionView):
    #template_name = 'word2def/game_play.html'

    def get_object(self, pk=None):
        return super(Word2DefQuestionView, self).get_object(pk='word2def')

    def make_question(self):
        level = 2  # TODO: Allow user to select level

        try:
            question, response = self.game.make_question(level=level)

            # Store data associated to 'response' and 'user_answer'
            #defs = [Definition(word=opt[0], definition=opt[1], level=level) for opt in response['options']]
            # Definition.objects.bulk_create(defs)
            for opt in response['options']:
                Definition.objects.get_or_create(word=opt[0], defaults={'definition': opt[1], 'level': level})

        except QuestionError as e:
            words = Definition.objects.all().order_by('?').values_list('word', 'definition')[:4]
            word, options, answer = self.game.get_random_question(words, 4)
            question, response = self.game.build_question(word, options, answer, level)

        return question, response

    def score(self, question, response, user_answer):
        score = super(Word2DefQuestionView, self).score(question, response, user_answer)

        # Store data associated to 'response' and 'user_answer'
        def_options = Definition.objects.filter(word__in=[it[0] for it in response['options']])

        r = response.get('answer')
        u = user_answer.get('answer', None)
        query = Definition.objects.get(word=response['options'][r][0])
        answer = Definition.objects.get(word=response['options'][int(u)][0])

        user = self.request.user if self.request.user and self.request.user.is_authenticated else None
        instance = Question(user=user, query=query, answer=answer, level=question['level'])
        instance.options = def_options
        instance.save(force_insert=True)

        return score

    def get_context_data(self, **kwargs):
        context = super(Word2DefQuestionView, self).get_context_data(**kwargs)
        answer_url = reverse('word2def:answer', kwargs={'uuid': self.uuid})
        context.update({'answer_url': answer_url, 'game': self.object})
        return context

