/// \file SteppingAction.hh
/// \brief Geantino Labs (IFPR), nov/2026 — grava passos no TrajectoryRecorder
///
/// No B5 um chuveiro hadronico de 1 GeV gera centenas de particulas. Para o
/// site, grava so:
///   - a particula primaria (sempre);
///   - secundarias com energia cinetica inicial >= minEnergy (padrao 20 MeV),
///     exceto neutrons e neutrinos (neutros de alcance longo, que encheriam
///     a cena de linhas sem interagir com os detectores).
/// Comando: /geantino/trajectories/minEnergy <valor> MeV

#ifndef GeantinoSteppingAction_h
#define GeantinoSteppingAction_h 1

#include "G4UserSteppingAction.hh"
#include "globals.hh"

class G4GenericMessenger;
class G4Track;

namespace Geantino
{

class SteppingAction : public G4UserSteppingAction
{
  public:
    SteppingAction();
    ~SteppingAction() override;

    void UserSteppingAction(const G4Step* step) override;

  private:
    G4bool ShouldRecord(const G4Track* track) const;

    G4double fMinEnergy;
    G4GenericMessenger* fMessenger = nullptr;
};

}  // namespace Geantino

#endif
