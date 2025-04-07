#!/usr/bin/perl

# This is the original script I wrote


use strict;
use warnings;
use File::Path qw(make_path);
use File::Copy qw(move);
use Cwd;
use Getopt::Long;


/**
 # remove single dashes at the beginning of a line
 perl -pi.bak -e 's/^-\s*(.*)$/$1/' pages/scratch.md 


  # remove lines with only dashes
  perl -pi.bak -e 's/^\s*-\s*$//' pages/scratch.md

**/

# Function to convert namespace-style filenames to directory structures recursively
sub convert_namespaces_to_directories {
    my ($dir) = @_;

    # Open the directory
    opendir(my $dh, $dir) or die "Cannot open directory $dir: $!";

    # Iterate over all files and directories in the current directory
    while (my $entry = readdir($dh)) {
        # Skip '.' and '..'
        next if ($entry eq '.' or $entry eq '..');
        
        my $path = "$dir/$entry";
        
        # If the entry is a directory, call the function recursively
        if (-d $path) {
            convert_namespaces_to_directories($path);
        } else {
            # Split the filename by double underscores
            my @parts = split /___/, $entry;
            
            # Ensure there is at least one part (filename)
            if (@parts) {
                # Extract the filename (last part)
                my $filename = pop @parts;
                
                # Create the target directory path
                my $new_dir = join('/', $dir, @parts);
                
                # Create the target directory if it doesn't exist
                unless (-d $new_dir) {
                    make_path($new_dir) or die "Failed to create path: $new_dir";
                }
                
                # Construct the full source and destination paths
                my $source_path = $path;
                my $target_path = "$new_dir/$filename";
                
                # Move the file
                move($source_path, $target_path) or die "Failed to move $source_path to $target_path: $!";
                
                print "Moved $source_path to $target_path\n";
            }
        }
    }

    # Close the directory handle
    closedir($dh);
}



sub convert_logseq_to_obsidian {
    my ($file_path) = @_;
    print "Converting Logseq properties to Obsidian properties in '$file_path'\n";

    
    # Open the input file for reading
    open my $in_fh, '<', $file_path or die "Cannot open '$file_path' for reading: $!";
    
    # Read all lines from the file
    my @lines = <$in_fh>;
    close $in_fh;

    # Array to store the converted lines
    my @converted_lines;
    my $properties_converted = 0;
    
    # Convert Logseq properties to Obsidian properties
    foreach my $line (@lines) {
        if ($line =~ /^([^:]+)::\s*(.*)$/) {
            my $key = $1;
            my $value = $2;
            push @converted_lines, "$key: $value\n";
            $properties_converted = 1;
        } else {
            # If a line does not match the Logseq property format, stop converting
            last;
        }
    }
    
    # If properties were converted, add YAML delimiters
    if ($properties_converted) {
        unshift @converted_lines, "---\n";
        push @converted_lines, "---\n";
    }
    
    # Append the rest of the original lines (unmodified part of the file)
    my $start_index = $properties_converted ? scalar(@converted_lines) - 1 : 0;
    for my $i ($start_index .. $#lines) {
        push @converted_lines, $lines[$i];
    }
    
    # Write the converted lines back to the file
    open my $out_fh, '>', $file_path or die "Cannot open '$file_path' for writing: $!";
    print $out_fh @converted_lines;
    close $out_fh;
    
    print "Converted properties in '$file_path'\n";
}


my $help;
my $convert_dirs;
my $convert_props;
my $convert_path;

GetOptions(
    'help' => \$help,
    'convert-dirs' => \$convert_dirs,
    'convert-props=s' => \$convert_path,
) or die "Invalid options passed to $0\n";

if ($help) {
    print "Usage: $0 --convert-dirs | --convert-props <file_path>\n";
    print "Options:\n";
    print "  --help              Show this help message\n";
    print "  --convert-dirs      Convert namespace-style filenames to directory structures\n";
    print "  --convert-props     Convert Logseq properties to Obsidian properties in the specified file\n";
    exit;
}

if ($convert_dirs) {
    my $current_dir = getcwd;
    convert_namespaces_to_directories($current_dir);
    print "Converted namespace-style filenames to directory structures in '$current_dir'\n";
}

if ($convert_path) {
    if (defined $convert_path) {
        convert_logseq_to_obsidian($convert_path);
    } else {
        die "You must provide a file path with --convert-props\n";
    }
}