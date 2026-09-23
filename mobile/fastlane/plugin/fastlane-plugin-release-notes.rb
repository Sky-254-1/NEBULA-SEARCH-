module Fastlane
  module Plugin
    class ReleaseNotesGenerator < Plugin
      class << self
        def generate_release_notes(version:, changes_file:)
          changes = File.read(changes_file) if File.exist?(changes_file)
          "## Version #{version}\n#{changes || 'Initial release'}"
        end
      end
    end
  end
end