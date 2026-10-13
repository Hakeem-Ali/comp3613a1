from app.services.rewards_service import RewardsService
from app.models.rewards import Milestone

class DummyRepo:
    def get_milestones(self):
        return []
    def award_milestone(self, *args, **kwargs):
        pass
    def get_user_milestones(self, *args, **kwargs):
        return []

service = RewardsService(DummyRepo())
milestones = [
    Milestone(id=1, name='Bronze Contributor', required_hours=10),
    Milestone(id=2, name='Silver Contributor', required_hours=40),
]
state = service.build_milestone_state(20, milestones)
assert state['current'] == 'Bronze Contributor'
assert state['next'] == 'Silver Contributor'
assert state['progress'] == 50.0
assert service.is_award_eligible(10, 4, []) is True
assert service.is_award_eligible(0, 4, []) is False
print('SERVICE_OK')
print(state)
