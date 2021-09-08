from canvas_stream.modules.drive.components.manager import DriveProcessor


processor = DriveProcessor()
processor.authenticate()
processor.read_files()

print(processor.__dict__)