/// \file SteppingAction.cc
/// \brief Geantino Labs (IFPR), nov/2026 — ver SteppingAction.hh

#include "SteppingAction.hh"

#include "TrajectoryRecorder.hh"

#include "G4Event.hh"
#include "G4EventManager.hh"
#include "G4Step.hh"
#include "G4SystemOfUnits.hh"
#include "G4Track.hh"

namespace Geantino
{

void SteppingAction::UserSteppingAction(const G4Step* step)
{
  auto track = step->GetTrack();
  auto particleDef = track->GetParticleDefinition();

  int eventID = G4EventManager::GetEventManager()->GetConstCurrentEvent()->GetEventID();
  int trackID = track->GetTrackID();
  const std::string& particleName = particleDef->GetParticleName();
  int charge = static_cast<int>(particleDef->GetPDGCharge());

  auto recorder = TrajectoryRecorder::Instance();

  // No primeiro passo, grava tambem o vertice (PreStepPoint), senao o
  // ponto de partida da trajetoria se perde.
  if (track->GetCurrentStepNumber() == 1) {
    auto pre = step->GetPreStepPoint()->GetPosition();
    recorder->AddPoint(eventID, trackID, particleName, charge, pre.x() / cm, pre.y() / cm,
                       pre.z() / cm);
  }

  auto post = step->GetPostStepPoint()->GetPosition();
  recorder->AddPoint(eventID, trackID, particleName, charge, post.x() / cm, post.y() / cm,
                     post.z() / cm);
}

}  // namespace Geantino
