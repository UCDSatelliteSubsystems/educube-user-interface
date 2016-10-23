from tornado.web import UIModule

class EduCubeTelemetry(UIModule):
    def javascript_files(self):
        return [
            # "bootstrap.min.js",
            # "jquery.js"
        ]

    def css_files(self):
        return [
            # "bootstrap.min.css",
            # "portfolio-item.css"
        ]

    def render(self, telemetry, show_comments=False):
        return self.render_string(
            "modules/telemetry.html", 
            telemetry=telemetry, 
            show_comments=show_comments)
