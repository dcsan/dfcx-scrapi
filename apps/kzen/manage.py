import unittest


def test():
    """Run the unit tests."""
    tests = unittest.TestLoader().discover('./tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

test()
