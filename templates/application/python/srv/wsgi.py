from srv.app import app as application

# Profiler initialization. It starts a daemon thread which continuously
# collects and uploads profiles. Best done as early as possible.
# try:
#     googlecloudprofiler.start(
#         service="rapidtest",
#         service_version="0.0.1",
#         # verbose is the logging level. 0-error, 1-warning, 2-info,
#         # 3-debug. It defaults to 0 (error) if not set.
#         verbose=2,
#     )
# except (ValueError, NotImplementedError, DefaultCredentialsError) as exc:
#     logging.error(exc)  # Handle errors here


if __name__ == "__main__":
    application.run()
