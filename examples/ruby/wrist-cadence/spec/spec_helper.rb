# frozen_string_literal: true

# RSpec configuration for wrist-cadence

# Coverage gate, activated by COVERAGE=true (scripts/test.sh --coverage
# and the CI workflow set it). This block is the SINGLE home of the
# >=90% line-coverage bound — scripts, hooks, and CI never restate the
# number. SimpleCov must start before the application code is loaded,
# which holds because every spec requires this helper first.
if ENV["COVERAGE"]
  require "simplecov"
  SimpleCov.start do
    add_filter "/spec/"
    minimum_coverage 90
  end
end

RSpec.configure do |config|
  # Use the expect syntax
  config.expect_with :rspec do |expectations|
    expectations.include_chain_clauses_in_custom_matcher_descriptions = true
  end

  # Use the new syntax for mocks
  config.mock_with :rspec do |mocks|
    mocks.verify_partial_doubles = true
  end

  # Enable color output
  config.color = true

  # Use the documentation formatter for detailed output
  config.default_formatter = "doc" if config.files_to_run.one?

  # Randomize test order
  config.order = :random
  Kernel.srand config.seed
end
