from app.domain.exceptions import ForbiddenError, NotFoundError


def require_owned_or_public_resource(resource, current_user, resource_name: str = "Resource"):
    if resource is None:
        raise NotFoundError(f"{resource_name} not found")
    owner_id = getattr(resource, "user_id", None)
    if owner_id is not None and (current_user is None or current_user.id != owner_id):
        raise ForbiddenError(f"{resource_name} access denied")
    return resource
