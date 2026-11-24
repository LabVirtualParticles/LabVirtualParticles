/// \file SteppingAction.cc
/// \brief Geantino Labs (IFPR), nov/2026 — ver SteppingAction.hh

#include "SteppingAction.hh"

#include "TrajectoryRecorder.hh"

#include "G4Event.hh"
#include "G4EventManager.hh"
#include "G4GenericMessenger.hh"
#include "G4ParticleDefinition.hh"
#include "G4Step.hh"
#include "G4SystemOfUnits.hh"
#include "G4Track.hh"

namespace Geantino
{

SteppingAction::SteppingAction() : fMinEnergy(20. * MeV)
{
  fMessenger = new G4GenericMessenger(this, "/geantino/trajectories/",
                                      "Quais trajetorias vao para o site");
  auto& cmd = fMessenger->DeclarePropertyWithUnit(
    "minEnergy", "MeV", fMinEnergy,
    "Energia cinetica inicial minima de uma secundaria para ser gravada");
  cmd.SetParameterName("minEnergy", false);
  cmd.SetRange("minEnergy>=0.");
}

SteppingAction::~SteppingAction()
{
  delete fMessenger;
}

G4bool SteppingAction::ShouldRecord(const G4Track* track) const
{
  if (track->GetParentID() == 0) return true;
  const auto& name = track->GetParticleDefinition()->GetParticleName();
  if (name == "neutron" || name == "anti_neutron" || name == "nu_e" || name == "anti_nu_e"
      || name == "nu_mu" || name == "anti_nu_mu" || name == "nu_tau" || name == "anti_nu_tau")
  {
    return false;
  }
  return track->GetVertexKineticEnergy() >= fMinEnergy;
}

void SteppingAction::UserSteppingAction(const G4Step* step)
{
  auto track = step->GetTrack();
  if (!ShouldRecord(track)) return;

  auto particleDef = track->GetParticleDefinition();
  int eventID = G4EventManager::GetEventManager()->GetConstCurrentEvent()->GetEventID();
  int trackID = track->GetTrackID();
  const std::string& particleName = particleDef->GetParticleName();
  int charge = static_cast<int>(particleDef->GetPDGCharge());

  auto recorder = TrajectoryRecorder::Instance();
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
