def average(numbers):
    return sum(numbers) / len(numbers)


def report(groups):
    return {name: average(values) for name, values in groups.items()}


if __name__ == "__main__":
    groups = {
        "alpha": [10, 20, 30],
        "beta": [],
        "gamma": [5, 5, 5],
    }
    print(report(groups))
