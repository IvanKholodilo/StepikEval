from StepikEval import CourseClassifier, Course

course = Course(CourseClassifier())
print(course.get_info('https://stepik.org/course/56237'))
print(course.positive, course.average_stars, len(course.reviews))