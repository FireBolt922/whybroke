class Config:
    def __init__(self, path):
        self.path = path
        self.loaded = False


def load(config):
    config.load()
    return config


if __name__ == "__main__":
    cfg = Config("/etc/app.yaml")
    load(cfg)
