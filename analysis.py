import re
from dataclasses import dataclass

@dataclass
class TestResult:
    test_type: str
    protocol: str
    iops: float
    bandwidth: float
    latency_avg: float
    latency_p99: float
    cpu_user: float
    cpu_system: float

def parse_fio_output(output):
    results = []
    current_protocol = None
    current_test = None

    for line in output.split('\n'):
        if line.startswith('Testing'):
            current_protocol = line.split()[-1]
        elif line.startswith('Running'):
            current_test = line.split()[1]
        elif 'iops' in line.lower():
            iops_match = re.search(r'IOPS=(\d+\.?\d*)', line)
            bw_match = re.search(r'BW=(\d+\.?\d*)(\w+)/s', line)
            if iops_match and bw_match:
                iops = float(iops_match.group(1))
                bw = float(bw_match.group(1))
                bw_unit = bw_match.group(2)
                if bw_unit == 'KiB':
                    bw /= 1024
                elif bw_unit == 'GiB':
                    bw *= 1024
        elif 'clat' in line and 'avg' in line:
            lat_match = re.search(r'avg=(\d+\.?\d*)', line)
            if lat_match:
                avg_lat = float(lat_match.group(1))
        elif '99.00th' in line:
            p99_match = re.search(r'99.00th=\[\s*(\d+\.?\d*)', line)
            if p99_match:
                p99_lat = float(p99_match.group(1))
        elif 'cpu' in line:
            cpu_match = re.search(r'usr=(\d+\.?\d*)%, sys=(\d+\.?\d*)%', line)
            if cpu_match:
                cpu_user = float(cpu_match.group(1))
                cpu_system = float(cpu_match.group(2))
                results.append(TestResult(current_test, current_protocol, iops, bw, avg_lat, p99_lat, cpu_user, cpu_system))

    return results

def analyze_results(results):
    nfs_results = {r.test_type: r for r in results if r.protocol == '/mnt/nfs/ds218/backups'}
    smb_results = {r.test_type: r for r in results if r.protocol == '/mnt/smb/ds218/backups'}

    print("Performance Comparison: NFS vs SMB")
    print("==================================")

    for test_type in nfs_results.keys():
        nfs = nfs_results[test_type]
        smb = smb_results[test_type]
        
        print(f"\n{test_type.upper()}:")
        print(f"  IOPS:        NFS: {nfs.iops:.2f}    SMB: {smb.iops:.2f}    Difference: {(smb.iops/nfs.iops - 1)*100:.2f}%")
        print(f"  Bandwidth:   NFS: {nfs.bandwidth:.2f} MiB/s    SMB: {smb.bandwidth:.2f} MiB/s    Difference: {(smb.bandwidth/nfs.bandwidth - 1)*100:.2f}%")
        print(f"  Avg Latency: NFS: {nfs.latency_avg:.2f} µs    SMB: {smb.latency_avg:.2f} µs    Difference: {(nfs.latency_avg/smb.latency_avg - 1)*100:.2f}%")
        print(f"  P99 Latency: NFS: {nfs.latency_p99:.2f} µs    SMB: {smb.latency_p99:.2f} µs    Difference: {(nfs.latency_p99/smb.latency_p99 - 1)*100:.2f}%")
        print(f"  CPU Usage:")
        print(f"    User:      NFS: {nfs.cpu_user:.2f}%    SMB: {smb.cpu_user:.2f}%    Difference: {smb.cpu_user - nfs.cpu_user:.2f}%")
        print(f"    System:    NFS: {nfs.cpu_system:.2f}%    SMB: {smb.cpu_system:.2f}%    Difference: {smb.cpu_system - nfs.cpu_system:.2f}%")
        print(f"    Total:     NFS: {nfs.cpu_user + nfs.cpu_system:.2f}%    SMB: {smb.cpu_user + smb.cpu_system:.2f}%    Difference: {(smb.cpu_user + smb.cpu_system) - (nfs.cpu_user + nfs.cpu_system):.2f}%")

    print("\nSummary:")
    for test_type in nfs_results.keys():
        nfs = nfs_results[test_type]
        smb = smb_results[test_type]
        faster = "SMB" if smb.iops > nfs.iops else "NFS"
        difference = (max(smb.iops, nfs.iops) / min(smb.iops, nfs.iops) - 1) * 100
        print(f"  {test_type}:")
        print(f"    Performance: {faster} is faster by {difference:.2f}%")
        cpu_difference = (smb.cpu_user + smb.cpu_system) - (nfs.cpu_user + nfs.cpu_system)
        cpu_efficient = "NFS" if cpu_difference > 0 else "SMB"
        print(f"    CPU Efficiency: {cpu_efficient} uses less CPU by {abs(cpu_difference):.2f}%")

with open('fio_output.txt', 'r') as f:
    fio_output = f.read()

results = parse_fio_output(fio_output)
analyze_results(results)
