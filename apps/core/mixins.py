from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Restringe el acceso a una vista según el rol del usuario (RBAC)."""

    allowed_roles = []

    def test_func(self):
        return getattr(self.request.user, 'role', '') in self.allowed_roles
