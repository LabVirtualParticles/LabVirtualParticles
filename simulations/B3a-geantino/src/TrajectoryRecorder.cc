/// \file TrajectoryRecorder.cc
/// \brief Geantino Labs (IFPR), nov/2026 — ver TrajectoryRecorder.hh

#include "TrajectoryRecorder.hh"

#include <fstream>

namespace Geantino
{

TrajectoryRecorder* TrajectoryRecorder::fInstance = nullptr;

TrajectoryRecorder* TrajectoryRecorder::Instance()
{
  if (!fInstance) fInstance = new TrajectoryRecorder();
  return fInstance;
}

void TrajectoryRecorder::AddPoint(int eventID, int trackID, const std::string& particleName,
                                  int charge, double x_cm, double y_cm, double z_cm)
{
  if (fPointCount >= kMaxPoints) {
    fTruncated = true;
    return;
  }
  const auto key = std::make_pair(eventID, trackID);
  auto it = fIndex.find(key);
  std::size_t pos;
  if (it == fIndex.end()) {
    pos = fTracks.size();
    fTracks.push_back(TrackRecord{eventID, trackID, particleName, charge, {}});
    fIndex.emplace(key, pos);
  }
  else {
    pos = it->second;
  }
  fTracks[pos].points.push_back({x_cm, y_cm, z_cm});
  ++fPointCount;
}

void TrajectoryRecorder::Clear()
{
  fTracks.clear();
  fIndex.clear();
  fPointCount = 0;
  fTruncated = false;
}

void TrajectoryRecorder::WriteJSON(const std::string& filename) const
{
  std::ofstream out(filename);
  out << "{\"truncated\": " << (fTruncated ? "true" : "false") << ", \"trajectories\": [";
  for (std::size_t i = 0; i < fTracks.size(); ++i) {
    const auto& t = fTracks[i];
    out << "{\"event\": " << t.event << ", \"track\": " << t.track << ", \"particle\": \""
        << t.particle << "\"" << ", \"charge\": " << t.charge << ", \"points\": [";
    for (std::size_t j = 0; j < t.points.size(); ++j) {
      const auto& p = t.points[j];
      out << "[" << p[0] << ", " << p[1] << ", " << p[2] << "]";
      if (j + 1 < t.points.size()) out << ", ";
    }
    out << "]}";
    if (i + 1 < fTracks.size()) out << ", ";
  }
  out << "]}";
}

}  // namespace Geantino
