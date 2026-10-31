def ministry(request):
    user = request.user
    authenticated = user.is_authenticated
    return {
        "church_short_name": "New Fadama SDA Church",
        "church_name": "New Fadama Seventh-day Adventist Church",
        "ministry_name": "Children's Ministries",
        "can_manage_records": authenticated and user.has_perm("children.add_child"),
        "can_take_attendance": authenticated and user.has_perm("attendance.add_attendance"),
        "can_manage_academic_year": authenticated and user.has_perm("schools.change_academicyear"),
        "can_add_visitor": authenticated
        and user.has_perm("visitors.add_visitor")
        and user.has_perm("visitors.add_visit"),
    }
